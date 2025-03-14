# HAMMER-VLSI PLUGIN, XCELIUM
# Notes: This plugin sets up xrun to execute in a three-step xrun invocation.
#        This bridges multi-tool direct-invocation and the xrun single-invocation.
#        As a primer, Xcelium currently supports three methods of running simulations:
#        1) Single call xrun: The recommended Cadence use-style that generates work and scratch dirs,
#           invokes appropriate compilers and settings based on input files, and generally simplifies the
#           simulation process.
#        2) Multi call xrun: Offers the ability to split the flow into 3 parts with added complications,
#           but is clearer when deep access to each step is required. Has all the utility of a direct
#           invocation use-style with the added convenience of single call xrun. Additionally, is required
#           when elaboration environment is preserved.
#        3) Direct invocation of xmvlog, xmelab, xmsim tools manually.

import os
import json
import datetime
import io
import re
import logging # Remove later to use hammer logging
from typing import Dict, List, Optional, Tuple, Any

import hammer.tech as hammer_tech
from hammer.vlsi import TimeValue
from hammer.vlsi import HammerSimTool, HammerToolStep, HammerLSFSubmitCommand, HammerLSFSettings
from hammer.logging import HammerVLSILogging
from hammer.common.cadence import CadenceTool
from hammer.utils import retrieve_files, sift_exts

# MXHammer version

class xcelium(HammerSimTool, CadenceTool):

  @property
  def xcelium_ext(self) -> List[str]:
    verilog_ext  = [".v", ".V", ".VS", ".vp", ".VP"]
    sverilog_ext = [".sv",".SV",".svp",".SVP",".svi",".svh",".vlib",".VLIB"]
    verilogams_ext = [".vams", ".VAMS", ".Vams", ".vAMS"]
    vhdl_ext = [".vhdl", ".VHDL"]
    scs_ext = [".scs", ".SCS", ".sp", ".SP"] 
    c_cxx_ext    = [".c",".cc",".cpp"]
    gz_ext       = [ext + ".gz" for ext in verilog_ext + sverilog_ext + verilogams_ext + scs_ext]
    z_ext        = [ext + ".z" for ext  in verilog_ext + sverilog_ext + verilogams_ext + scs_ext]
    return (verilog_ext + sverilog_ext + verilogams_ext + vhdl_ext + scs_ext + c_cxx_ext + gz_ext + z_ext)

  @property
  def steps(self) -> List[HammerToolStep]:
    return self.make_steps_from_methods([self.compile_xrun,
                                         self.elaborate_xrun,
                                         self.sim_xrun])

  def tool_config_prefix(self) -> str:
    return "sim.xcelium"
  
  @property
  def sim_input_prefix(self) -> str:
    return "sim.inputs"
  
  @property
  def sim_waveform_prefix(self) -> str:
    return "sim.inputs.waveform"
  
  @property
  def xcelium_bin(self) -> str:
    return self.get_setting("sim.xcelium.xcelium_bin")
  
  @property
  def spectre_bin(self) -> str:
    return self.get_setting("sim.xcelium.spectre_bin")

  @property
  def sim_tcl_file(self) -> str: 
    return os.path.join(self.run_dir, "xrun_sim.tcl")
    
  @property
  def sdf_cmd_file(self) -> str:
    return os.path.join(self.run_dir, "design.sdf_cmd")

  @property
  def post_synth_sdc(self) -> Optional[str]:
    pass
  
  def get_verilog_models(self) -> List[str]:
    verilog_sim_files = self.technology.read_libs([
        hammer_tech.filters.verilog_sim_filter], 
        hammer_tech.HammerTechnologyUtils.to_plain_item)
    return verilog_sim_files
        
  def fill_outputs(self) -> bool:
    saif_opts = self.extract_saif_opts()
    wav_opts = self.extract_waveform_opts()[1]

    self.output_waveforms = []
    self.output_saifs = []
    self.output_top_module = self.top_module
    self.output_tb_name = self.get_setting(f"{self.sim_input_prefix}.tb_name")
    self.output_tb_dut  = self.get_setting(f"{self.sim_input_prefix}.tb_dut")
    self.output_level   = self.get_setting(f"{self.sim_input_prefix}.level")
    
    if saif_opts ["mode"] is not None:
      self.output_saifs.append(os.path.join(self.run_dir, "ucli.saif"))
    if wav_opts["type"] is not None:
      extension = wav_opts["type"].lower()
      self.output_waveforms.append(os.path.join(self.run_dir, f'{wav_opts["dump_name"]}.{extension}'))

    return True
  
  # Several extract functions are used to process mandatory keys into string options. 
  # Returns a raw input dictionary as well.

  def extract_xrun_opts(self) -> Tuple[Dict[str, str], Dict[str, str]]:
    xrun_opts_def = {"enhanced_recompile": True,
                     "xmlibdirname": None,
                     "xmlibdirpath": None,
                     "simtmp": None,
                     "snapshot": None,
                     "global_access": False,
                     "mce": False}

    xrun_opts = self.get_settings_from_dict(xrun_opts_def ,key_prefix=self.tool_config_prefix())
    xrun_opts_proc = xrun_opts.copy()
    bool_list = ["global_access", "enhanced_recompile", "mce", "ams"]
    
    if xrun_opts_proc ["global_access"]: 
      xrun_opts_proc ["global_access"] = "+access+rcw"
    else:
      xrun_opts_proc ["global_access"] = ""
      
    if xrun_opts_proc ["enhanced_recompile"]:
      xrun_opts_proc ["enhanced_recompile"] = "-fast_recompilation"
    else:
      xrun_opts_proc ["enhanced_recompile"] = ""

    if xrun_opts_proc ["mce"]:
      xrun_opts_proc ["mce"] = "-mce"
    else:
      xrun_opts_proc ["mce"] = ""
    
    for opt, setting in xrun_opts_proc.items():
      if opt not in bool_list and setting is not None:
        xrun_opts_proc [opt] = f"-{opt} {setting}"
    
    return xrun_opts_proc, xrun_opts 
  
  def extract_sim_opts(self) -> Tuple[Dict[str, str], Dict[str, str]]:
    abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
    sim_opts_def = {"tb_name": None,
                    "tb_dut": None,
                    "timescale": None,
                    "defines": None,
                    "incdir": None,
                    "execute_sim": True,
                    "compiler_cc_opts": None,
                    "compiler_ld_opts": None}
    
    # Defines and incdir are not strictly necessary.
    optional_keys = ["defines", "incdir", "compiler_cc_opts", "compiler_ld_opts"]
    sim_opts = self.get_settings_from_dict(sim_opts_def, self.sim_input_prefix, optional_keys)
    # Additional keys required if GL.
    if self.level.is_gatelevel(): 
      sim_opts ["gl_register_force_value"] = self.get_setting(f"{self.sim_input_prefix}.gl_register_force_value", 0)
      sim_opts ["timing_annotated"] = self.get_setting(f"{self.sim_input_prefix}.timing_annotated", False)

    sim_opts_proc = sim_opts.copy()
    sim_opts_proc ["input_files"] =  "\n".join([input for input in abspath_input_files])
    sim_opts_proc ["tb_name"]   = "-top " + sim_opts_proc ["tb_name"]
    sim_opts_proc ["timescale"] = "-timescale " + sim_opts_proc ["timescale"]
    if sim_opts_proc ["defines"] is not None: sim_opts_proc ["defines"] = "\n".join(["-define " + define for define in sim_opts_proc ["defines"]]) 
    if sim_opts_proc ["incdir"] is not None:  sim_opts_proc ["incdir"]  = "\n".join(["-incdir " + incdir for incdir in sim_opts_proc ["incdir"]]) 
    if sim_opts_proc ["compiler_cc_opts"] is not None: sim_opts_proc ["compiler_cc_opts"] = "\n".join(["-Wcxx," + opt for opt in sim_opts_proc ["compiler_cc_opts"]]) 
    if sim_opts_proc ["compiler_ld_opts"] is not None: sim_opts_proc ["compiler_ld_opts"] = "\n".join(["-Wld," + opt for opt in sim_opts_proc ["compiler_ld_opts"]]) 

    return sim_opts_proc, sim_opts

  def extract_waveform_opts(self) -> Tuple[Dict[str, str], Dict[str, str]]:
    wav_opts_def = {"type": None,
                    "dump_name": "waveform",
                    "compression": False,
                    "probe_paths": None,
                    "tcl_opts": None,
                    "shm_incr": "5G"}
    
    # Because key-driven waveform spec is optional, should return none-type dict by default.
    wav_opts: Dict[str, Any] = {}
    if self.get_setting(f"{self.sim_waveform_prefix}.type") is not None:
      optional_keys = ["shm_incr"]
      wav_opts = self.get_settings_from_dict(wav_opts_def, self.sim_waveform_prefix, optional_keys)
      wav_opts_proc = wav_opts.copy()
      wav_opts_proc ["compression"] = "-compress" if wav_opts ["compression"] else ""
      if wav_opts_proc ["probe_paths"] is not None: wav_opts_proc ["probe_paths"] = "\n".join(["probe -create " + path for path in wav_opts_proc ["probe_paths"]]) 
      if wav_opts_proc ["tcl_opts"] is not None:    wav_opts_proc ["tcl_opts"]    = "\n".join(opt for opt in wav_opts_proc ["tcl_opts"]) 
    else: 
      wav_opts = {"type": None}
      wav_opts_proc = wav_opts.copy()
    
    return wav_opts_proc, wav_opts

  def extract_saif_opts(self) -> Dict[str, str]:

    saif_opts = {}
    saif_opts ["mode"] = self.get_setting(f"{self.sim_input_prefix}.saif.mode")

    if saif_opts ["mode"] == "time":
      saif_opts ["start_time"] = self.get_setting(f"{self.sim_input_prefix}.saif.start_time")
      saif_opts ["end_time"]   = self.get_setting(f"{self.sim_input_prefix}.saif.end_time")
    if saif_opts ["mode"] == "trigger_raw":
      saif_opts ["start_trigger_raw"] = self.get_setting(f"{self.sim_input_prefix}.saif.start_trigger_raw")
      saif_opts ["end_trigger_raw"]   = self.get_setting(f"{self.sim_input_prefix}.saif.end_trigger_raw")
    return saif_opts

  # Label generated files
  def write_header(self, header: str, wrapper: io.TextIOWrapper)->None:
    now = datetime.datetime.now()
    wrapper.write("# "+"="*39+"\n")
    wrapper.write("# "+header+"\n")
    wrapper.write(f"# CREATED AT {now} \n")
    wrapper.write("# "+"="*39+"\n")

  # LSF submit command 
  # Try to maintain some parity with vcs plugin. 
  def update_submit_options(self)->None:
    if isinstance(self.submit_command, HammerLSFSubmitCommand):
        settings = self.submit_command.settings._asdict()
        if self.submit_command.settings.num_cpus is not None:
          settings['num_cpus'] = self.submit_command.settings.num_cpus
        else: 
          settings['num_cpus'] = 1
        self.submit_command.settings = HammerLSFSettings(**settings)
    else:
      pass
    
  # Create an xrun.arg file
  def generate_arg_file(self, 
                        file_name: str, 
                        header: str, 
                        additional_opt: List[Tuple[str, List[str]]] = [],
                        sim_opt_removal: List[str]=[],
                        xrun_opt_removal: List[str]=[]) -> str:

    # Xrun opts and sim opts must generally be carried through for 1:1:1 correspondence between calls.
    # However, certain opts must be removed (e.g., during sim step), leading to the inclusion of removal opts.
    xrun_opts_proc = self.extract_xrun_opts()[0]
    sim_opts_proc  = self.extract_sim_opts()[0]
    sim_opt_removal.extend(["tb_dut", "execute_sim", "gl_register_force_value", "timing_annotated"]) # Always remove these.
    [xrun_opts_proc.pop(opt, None) for opt in xrun_opt_removal]
    [sim_opts_proc.pop(opt, None) for opt in sim_opt_removal]
    
    arg_path  = self.run_dir+f"/{file_name}"
    f = open(arg_path,"w+")
    self.write_header(header, f)    
    
    f.write("\n# XRUN OPTIONS: \n")
    [f.write(elem + "\n") for elem in xrun_opts_proc.values() if elem is not None]
    f.write("\n# SIM OPTIONS: \n")
    [f.write(elem + "\n") for elem in sim_opts_proc.values() if elem is not None]
    for opt_list in additional_opt: 
      if opt_list[1]: 
        f.write(f"\n# {opt_list[0]} OPTIONS: \n")
        [f.write(elem + "\n") for elem in opt_list[1]]
    f.close()  
    
    return arg_path

  
  
  # Convenience function invoked when multicore options are needed.
  def generate_mc_cmd(self) -> str:
    opts = ""
    num_threads=int(self.get_setting("vlsi.core.max_threads")) - 1
    opts = opts + f"-mce_build_thread_count {num_threads} \n"
    opts = opts + f"-mce_sim_thread_count {num_threads} \n"
    return opts
  
  # Deposit values
  # Try to maintain some parity with vcs plugin.
  def generate_gl_deposit_tcl(self) -> List[str]:
    sim_opts  = self.extract_sim_opts() [1]
    tb_prefix = sim_opts["tb_name"] + '.' + sim_opts["tb_dut"]
    force_val = sim_opts["gl_register_force_value"]
    
    abspath_all_regs = os.path.join(os.getcwd(), self.all_regs)
    if not os.path.isfile(abspath_all_regs):
      self.logger.error("List of all regs json not found as expected at {0}".format(self.all_regs))

    formatted_deposit = []
    with open(abspath_all_regs) as reg_file:
      reg_json = json.load(reg_file)
      assert isinstance(reg_json, List), "list of all sequential cells should be a json list of dictionaries from string to string not {}".format(type(reg_json))
      for reg in sorted(reg_json, key=lambda r: len(r["path"])): 
        path = reg["path"]
        path = path.split('/')
        special_char =['[',']','#','$',';','!',"{",'}','\\']
        path = ['@{' + subpath + ' }' if any(char in subpath for char in special_char) else subpath for subpath in path]
        path='.'.join(path)
        pin = reg["pin"]
        formatted_deposit.append("deposit " + tb_prefix + "." + path + "." + pin + " = " + str(force_val))
        
    return formatted_deposit

  # Creates an sdf cmd file for command line driven sdf annotation.
  # Until sdf annotation provides values other than maximum, sdf_cmd_file will only support mtm max.
  def generate_sdf_cmd_file(self) -> bool:
    sim_opts  = self.extract_sim_opts()[1]
    prefix = sim_opts["tb_name"] + '.' + sim_opts["tb_dut"]

    f = open(self.sdf_cmd_file,"w+")
    f.write(f'SDF_FILE = "{self.sdf_file}", \n')
    f.write(f'MTM_CONTROL = "MAXIMUM", \n')
    f.write(f'SCALE_TYPE = "FROM_MAXIMUM", \n')
    f.write(f'SCOPE = {prefix};')
    f.close()
    return True

  # Creates saif arguments for tcl commands for tcl driver.
  def generate_saif_tcl_cmd(self) -> str:
    saif_opts: Dict[str, Any] = self.extract_saif_opts()
    sim_opts  = self.extract_sim_opts()[1]
    prefix = sim_opts["tb_name"] + '.' + sim_opts["tb_dut"]

    saif_args = ""

    # Process saif options
    saif_start_time: Optional[str] = None
    saif_end_time: Optional[str] = None
    saif_start_trigger_raw: Optional[str] = None
    saif_end_trigger_raw: Optional[str] = None
    if saif_opts["mode"] == "time":
      saif_start_time = saif_opts["start_time"]
      saif_end_time   = saif_opts["end_time"]
    elif saif_opts["mode"] == "trigger":
      self.logger.error("Trigger SAIF mode currently unsupported.")
    elif saif_opts["mode"] == "full":
      pass
    elif saif_opts["mode"] == "trigger_raw":
      saif_start_trigger_raw = saif_opts["start_trigger_raw"]
      saif_end_trigger_raw   = saif_opts["end_trigger_raw"]
    else:
      self.logger.warning("Bad saif_mode:${saif_mode}. Valid modes are time, full, trigger, or none. Defaulting to none.")
      saif_opts["mode"] = None
    
    if saif_opts["mode"] is not None: 
      if saif_opts["mode"] == "time":
        assert saif_start_time
        assert saif_end_time
        stime = TimeValue(saif_start_time)
        etime = TimeValue(saif_end_time)
        saif_args = saif_args + f'dumpsaif -output ucli.saif -overwrite -scope {prefix} -start {stime.value_in_units("ns")}ns -stop{etime.value_in_units("ns")}ns'
      elif saif_opts["mode"] == "full":
        saif_args = saif_args + f"dumpsaif -output ucli.saif -overwrite -scope {prefix}"
      elif saif_opts["mode"] == "trigger_raw":
        assert saif_start_trigger_raw
        assert saif_end_trigger_raw
        saif_args = saif_args + f"dumpsaif -output ucli.saif -overwrite -scope {prefix} {saif_start_trigger_raw} {saif_end_trigger_raw}"
    return saif_args

  # Creates a tcl driver for simulation.
  def generate_sim_tcl(self) -> bool:
    xmsimrc_def = self.get_setting("sim.xcelium.xmsimrc_def")
    saif_opts   = self.extract_saif_opts()
    wav_opts_proc, wav_opts = self.extract_waveform_opts()

    f = open(self.sim_tcl_file,"w+")
    self.write_header("HAMMER-GEN SIM TCL DRIVER", f)    
    f.write(f"source {xmsimrc_def} \n")
    
    # Prepare waveform dump options if specified.
    if wav_opts["type"] is not None:
      if wav_opts["type"]   == "VCD":  f.write(f'database -open -vcd vcddb -into {wav_opts["dump_name"]}.vcd -default {wav_opts_proc["compression"]} \n')
      elif wav_opts["type"] == "EVCD": f.write(f'database -open -evcd evcddb -into {wav_opts["dump_name"]}.evcd -default {wav_opts_proc["compression"]} \n')
      elif wav_opts["type"] == "SHM":  f.write(f'database -open -shm shmdb -into {wav_opts["dump_name"]}.shm -event -default {wav_opts_proc["compression"]} {wav_opts_proc["shm_incr"]} \n')
      if wav_opts_proc["probe_paths"] is not None: 
        [f.write(f'{wav_opts_proc["probe_paths"]}\n')]
      if wav_opts_proc["tcl_opts"] is not None: [f.write(f'{wav_opts_proc["tcl_opts"]}\n')]
    
    # Deposit gl values.
    if self.level.is_gatelevel(): 
      formatted_deposit = self.generate_gl_deposit_tcl()
      [f.write(f'{deposit}\n') for deposit in formatted_deposit]

    # Create saif file if specified.
    if saif_opts["mode"] is not None:
      f.write(f'{self.generate_saif_tcl_cmd()}\n')
    
    # Execute
    f.write("run \n")
    
    # Close databases and dumps properly.
    f.write("dumpsaif -end \n")
    f.write("database -close *db \n")
    f.write("exit")
    f.close()  
    return True

  """def generate_amscf(self) -> bool:
    # Open AMS control file template for read.
    # Hardcoded path for now
    t = open("amscf_template.scs", "r")

    # Create AMS control file (or overwrite if one already exists) for read/write.
    # Hardcoded path for now.
    f = open(f"./src/amscf.scs", "w+")

    # Get absolute paths for analog models from PDK and schematics from extralibs, respectively.
    model_path = self.get_setting("sim.xcelium.anamodels")
    models = [modelfile for modelfile in os.scandir(model_path)]
    schematic_path = self.get_setting("sim.xcelium.schematics")
    schematics = [schematic for schematic in os.scandir(schematic_path)]

    # Get list of paths to individual files within the PDK models (?) and schematic directories, respectively.
    #models = []
    #schematics = []

    # Warnings for missing files.
    if (len(schematics) > 0 and len(models) == 0):
      self.logger.warning(f"No models found in {model_path} to support analog schematics.")
    else:
      if (len(models) == 0):
        self.logger.warning(f"No models found in {model_path}.")
      if (len(schematicpath) == 0):
        self.logger.warning(f"No analog schematics found {schematics}.")

    # Get string representation of AMS control file template.
    template = t.read()

    # Format modelpaths list as a single string with include statements.
    formatted_models = ""
    for modelpath in models:
      formatted_models += f"include {modelpath}"
    
    # Format schematicpaths list as a single string with include statements.
    formatted_schematics = ""
    for schematicpath in schematics:
      formatted_schematics += f"include {schematicpath}"

    # Replace empty model deck with formatted string of model paths.
    template = re.sub("// model deck\n", "// model deck\n" + formatted_models)

    # Replace empty schematic deck with formatted string of schematic paths.
    template = re.sub("// schematic deck\n", "// schematic deck\n" + formatted_schematics)

    # Write filled template to AMS control file.
    f.write(template)

    # Close files properly.
    t.close()
    f.close()
    return True"""

  def attach_opts(self, filepath, attachment):
    f = open(filepath, "a+")
    f.write(attachment)
    f.close
    return 
  
  def get_disciplines(self) -> str:
    ### Read in disciplines file, if it exists.
    disciplines = self.get_setting("sim.xcelium.disciplines")
    cwd = os.getcwd()
    dpath = os.path.join(cwd, disciplines)
    if disciplines:
      df = open(dpath, "r")
      discipline_opts = df.read() + "\n"
      df.close()
      return discipline_opts
    else:
      return ""

  def compile_xrun(self) -> bool:
    
    if not os.path.isfile(self.xcelium_bin):
      self.logger.error(f"Xcelium (xrun) binary not found at {self.xcelium_bin}.")
      return False
  
    if not self.check_input_files(self.xcelium_ext):
      return False

    # Gather complation-only options
    xrun_opts     = self.extract_xrun_opts()[1]
    compile_opts  = self.get_setting(f"{self.tool_config_prefix()}.compile_opts", [])
    compile_opts.append("-logfile xrun_compile.log")
    if xrun_opts["mce"]: compile_opts.append(self.generate_mc_cmd())
    compile_opts  = ('COMPILE', compile_opts)
    
    arg_file_path = self.generate_arg_file("xrun_compile.arg", "HAMMER-GEN XRUN COMPILE ARG FILE", [compile_opts])
    args =[self.xcelium_bin]
    args.append(f"-compile -f {arg_file_path}")
    
    self.update_submit_options()  

    ### If AMS enabled, submit options but do not run compile sub-step.
    if self.get_setting(f"{self.tool_config_prefix()}.ams"):
      return True
    
    self.run_executable(args, cwd=self.run_dir)
    HammerVLSILogging.enable_colour = True
    HammerVLSILogging.enable_tag = True
    return True
    
  def elaborate_xrun(self) -> bool: 
    xrun_opts = self.extract_xrun_opts()[1]
    sim_opts  = self.extract_sim_opts()[1]
    elab_opts = self.get_setting(f"{self.tool_config_prefix()}.elab_opts", [])
    elab_opts.append("-logfile xrun_elab.log")
    elab_opts.append("-glsperf")
    elab_opts.append("-genafile access.txt")  
    
    if self.level.is_gatelevel():
      elab_opts.extend(self.get_verilog_models())    
      if sim_opts["timing_annotated"]:
        self.generate_sdf_cmd_file()
        elab_opts.append(f"-sdf_cmd_file {self.sdf_cmd_file}")  
        elab_opts.append("-sdf_verbose")
        elab_opts.append("-negdelay")
      else:
        elab_opts.append("-notimingchecks")
        elab_opts.append("-delay_mode zero")
    else:
      elab_opts.append("-notimingchecks")
      elab_opts.append("-delay_mode zero")
      
    if xrun_opts["mce"]: elab_opts.append(self.generate_mc_cmd())
    elab_opts = ('ELABORATION', elab_opts)

    
        
    arg_file_path = self.generate_arg_file("xrun_elab.arg", "HAMMER-GEN XRUN ELAB ARG FILE", [elab_opts])
    args =[self.xcelium_bin]
    args.append(f"-elaborate -f {arg_file_path}")

    self.update_submit_options()
    ### If AMS enabled, submit options but do not run elaborate sub-step.
    if self.get_setting(f"{self.tool_config_prefix()}.ams"):
      return True
    
    self.run_executable(args, cwd=self.run_dir)
    return True

  def sim_xrun(self) -> bool:
    sim_opts  = self.extract_sim_opts()[1]
    sim_cmd_opts = self.get_setting(f"{self.sim_input_prefix}.options", [])
    sim_opts_removal  = ["tb_name", "input_files", "incdir"]
    xrun_opts_removal = ["enhanced_recompile", "mce"]
    sim_cmd_opts = ('SIMULATION', sim_cmd_opts)
    
    if not sim_opts["execute_sim"]:
      self.logger.warning("Not running any simulations because sim.inputs.execute_sim is unset.")
      return True
    
    arg_file_path = self.generate_arg_file("xrun_sim.arg", "HAMMER-GEN XRUN SIM ARG FILE", [sim_cmd_opts],
                                           sim_opt_removal = sim_opts_removal,
                                           xrun_opt_removal = xrun_opts_removal)    
    args =[self.xcelium_bin]
    args.append(f"-R -f {arg_file_path} -input {self.sim_tcl_file}")

    self.generate_sim_tcl() 
    self.update_submit_options()
    self.run_executable(args, cwd=self.run_dir)
    return True

  def retrieve_file_list(self, path, exts=[], relative=True) -> list:
    file_list = []
    extslower = [extension.lower() for extension in exts]
    exts_proc = [f".{ext}" if ("." not in ext) else ext for ext in extslower]

    for (root, directories, filenames) in os.walk(path):
        for filename in filenames:
            file_ext = (os.path.splitext(filename)[1]).lower()
            rel_root = os.path.relpath(root)
            if (relative):
              filepath = os.path.join(rel_root, filename)
            else:
              filepath = f"{os.path.join(root, filename)}"

            if (not exts):
               file_list.append(filepath)
            elif (file_ext in exts_proc):
               file_list.append(filepath)
    
    return file_list

  
  

  def vlog_preparer(self, collect=False, sourcelist=[], sourcedir="", blacklist=[]) -> str:
      """
      Returns a formatted string of all verilog/VHDL files in the source
      """
      vlog = ""
      if (collect):
        sourcepath = os.path.join(os.getcwd(), sourcedir)
        vlog_list = self.retrieve_file_list(sourcepath, [".v", ".vhdl"])
      else:
        vlog_list = sift_exts(sourcelist, [".v"])

      if (blacklist and vlog_list):
        for pathname in blacklist:
          if pathname in vlog_list:
            vlog_list.remove(pathname)

      if vlog_list:
          vlog = " \\\n".join(vlog_list) + " \\\n"
        
      return f"{vlog}"

  def vams_preparer(self, collect=False, sourcelist=[], sourcedir="", blacklist=[]) -> str:
      """
      Returns a formatted string of all V-AMS files in the source
      """
      vams = ""
      if (collect):
        sourcepath = os.path.join(os.getcwd(), sourcedir)
        vams_list = self.retrieve_file_list(sourcepath, [".vams"])
      else:
        vams_list = sift_exts(sourcelist, [".vams"])

      if (blacklist and vams_list):
        for pathname in blacklist:
          if pathname in vams_list:
            vams_list.remove(pathname)

      if vams_list:
          vams = " \\\n".join(vams_list) + " \\\n"

      return f"{vams}"

  def analog_preparer(self, collect=False, sourcelist=[], sourcedir="", blacklist=[]) -> str:
      """
      Returns a formatted string of all analog (.scs) files in the source
      """
      control = ""
      if (collect):
        sourcepath = os.path.join(os.getcwd(), sourcedir)
        control_list = self.retrieve_file_list(sourcepath, [".scs"])
      else:
        control_list = sift_exts(sourcelist, [".scs"])
      
      if (blacklist and control_list):
        for pathname in blacklist:
          if pathname in control_list:
            control_list.remove(pathname)
      
      if control_list:
          control = " \\\n".join(control_list) + " \\\n"

      return f"{control}"

  def discipline_collector(self, discipline_filename) -> str:
      """
      Returns a formatted string of all disciplines from the disciplines.txt file
      """
      ### Read in disciplines file, if it exists.
      
  
      dpath = os.path.join(os.getcwd(), discipline_filename)

      if not os.path.isfile(dpath):
        self.logger.error(f"No discipline file found at {dpath}.")

      if dpath:
        df = open(dpath, "r")
        discipline_opts = df.read()
        disciplines_formatted = re.sub("\n", " \\\n", discipline_opts) + " \\"
        df.close()
        return disciplines_formatted
      else:
        return ""

  def option_preparer(self, opts, addt_opts, pseudo_step=True) -> str:
      """
      Returns a formatted string of all provided AMS options and their arguments
      """
      bool_list = ["ams", "disciplines", "gen_amscf"]
      opts_proc = opts.copy()
      header = ""

      if not opts:
        return ""

      if opts ["ams"] is True:
          opts_proc ["ams"] = "-ams_flex" + " \\"
      else:
        opts_proc ["ams"] = ""
      
      if opts ["gen_amscf"] is True:
        self.generate_amscf(self.get_setting("sim.xcelium.amscf_template"), self.get_setting("sim.xcelium.amscf")) # Expect names, not filepaths
        opts_proc ["gen_amscf"] = ""
      else:
        opts_proc ["gen_amscf"] = ""

      if opts ["disciplines"]:
        header += self.discipline_collector(opts["disciplines"]) + "\n"
      
      if opts ["amsconnrules"]:
        opts_proc ["amsconnrules"] = opts["amsconnrules"]

      if (pseudo_step):
          digital_opts = self.option_extractor(["xrun_compile.arg", "xrun_elab.arg", "xrun_sim.arg"])
          digital_opts.update(opts_proc) # Should any keys match, AMS arguments take precedence
          opts_proc = digital_opts

      opts_proc = {opt:setting for (opt, setting) in opts_proc.items() if opt not in bool_list and setting is not None}

      opts_len = len(opts_proc) - 1
      for (n, (opt, setting)) in enumerate(opts_proc.items()):
        if (n == opts_len):
            if (setting == ""):
                opts_proc [opt] = f"-{opt}"
            else:
                opts_proc [opt] = f"-{opt} {setting}"
        else:
          if (setting == ""):
              opts_proc [opt] = f"-{opt} \\"
          else:
              opts_proc [opt] = f"-{opt} {setting} \\"


      opts_rev = {k: v for k, v in opts_proc.items() if v}

      opts_proc_str = "\n".join(opts_rev.values())

      # Attach user-defined commands, if any are included
      if (addt_opts):
        opts_proc_str += " \\\n"

      footer = " \\\n".join(addt_opts)

      return header + f"{opts_proc_str}" + footer

  def generate_amscf(self, template_filename, amscontrol_filename) -> bool:
      """
      Creates an AMS control file based on templated format with available analog models & schematics
      """
      
      # Get analog models, schematics from directories specified in extralibs
      extralib = self.get_setting("vlsi.technologies.extra_libraries")
      extralib_dict = extralib[0]
      anamodels_dir = extralib_dict["anamodels"]
      schematics_dir = extralib_dict["schematics"]


      # Open AMS control file template for read.
      template_path = os.path.join(os.getcwd(), template_filename)
      t = open(template_path, "r")

      # Create AMS control file (or overwrite if one already exists) for read/write.
      amscontrol_path = os.path.join(os.getcwd(), amscontrol_filename)
      f = open(amscontrol_path, "w+")

      # Get normalized, absolute paths for analog model files
      model_path = os.path.join(os.getcwd(), anamodels_dir)
      models = [os.path.normpath(modelfile.path) for modelfile in os.scandir(model_path)]

      # Get normalized, absolute paths for analog schematic files
      schematic_path = os.path.join(os.getcwd(), schematics_dir)
      schematics = [os.path.normpath(schematic.path) for schematic in os.scandir(schematic_path)]

      # Warnings for missing files.
      if (len(schematics) > 0 and len(models) == 0):
        logging.warning(f"No models found in {model_path} to support analog schematics.")
      else:
        if (len(models) == 0):
          logging.warning(f"No models found in {model_path}.")
        if (len(schematic_path) == 0):
          logging.warning(f"No analog schematics found {schematics}.")

      # Get string representation of AMS control file template.
      template = t.read()

      # Format model_paths list as a single string with include statements.
      formatted_models = ""
      for modelpath in models:
        formatted_models += f"include {modelpath!r}\n"
      # Format schematic_paths list as a single string with include statements.
      formatted_schematics = ""
      for schematicpath in schematics:
        formatted_schematics += f"include {schematicpath!r}\n"

      # Replace empty model deck with formatted string of model paths.
      model_template = re.sub("// model deck\n", "// model deck\n" + formatted_models, template)

      # Replace empty schematic deck with formatted string of schematic paths.
      schematic_template = re.sub("// schematic deck\n", "// schematic deck\n" + formatted_schematics, model_template)

      # Write filled template to AMS control file.
      f.write(schematic_template)

      # Close files properly.
      t.close()
      f.close()
      return True
  
  def option_extractor(self, argfile_names=[]):
    if not argfile_names:
      return {}

    opts = {}
    
    # Extract the options from each argfile listed, ignoring duplicate opts and file inclusions
    for filename in argfile_names:
      path = os.path.join(self.run_dir, filename) 
      file_opts = {}
      f = open(path, "r")

      for line in f:
        if (line[0] == "-"):
          split_line = line.split(sep=None, maxsplit=2)
          if (len(split_line) > 1):
            opt_key, opt_arg = split_line[0].strip("- "), split_line[1].lstrip("\n")
          else:
            opt_key, opt_arg = split_line[0].strip("- "), ""
          
          file_opts[opt_key] = opt_arg

      opts.update(file_opts)
      f.close()

    return opts

  def scriptwriter(self, options, additional_options, collect=False, sourcedir="", blacklist=[], sourcelist=[]):
    """
    Writes all prepared files and arguments to the run_mxh shell script
    """
    runpath = os.path.join(self.run_dir, "run_mxh")

    f = open(runpath, "w+")

    # Write Shebang + xrun clean
    f.write("#!/bin/csh -f\n#\nxrun -clean \\\n")
    
    # Write Digital Files
    f.write(self.vlog_preparer(collect, sourcelist, sourcedir, blacklist))
    f.write(self.vams_preparer(collect, sourcelist, sourcedir, blacklist))

    # Write Analog Files
    f.write(self.analog_preparer(collect, sourcelist, sourcedir, blacklist))

    # Write Options
    f.write(self.option_preparer(options, additional_options))

    f.close()
    return

  def name_finder(self, name, sourcelist):
    # Helper function, should probably be moved later
    sourcelist_proc = [element.lower() for element in sourcelist if (type(element) == str)]
    for element in sourcelist_proc:
        if (name in element):
            return element
    
    return ""

  def run_mxh_pseudo_three_step(self) -> bool:
    if not os.path.isfile(self.xcelium_bin):
      self.logger.error(f"Xcelium (xrun) binary not found at {self.xcelium_bin}.")
      return False
  
    if not self.check_input_files(self.xcelium_ext):
      return False
    
    digital_files = self.get_setting("sim.inputs.input_files")
    acf = self.get_setting("sim.xcelium.acf")
    amscf = self.get_setting("sim.xcelium.amscf")

    # Extralibs Autorecognition
    extralib = self.get_setting("vlsi.technologies.extra_libraries")
    extralib_dict = extralib[0]
    
    #ams_opts = self.get_setting("sim.xcelium.ams_opts")

    #source = digital_files + [acf, amscf, connectlibs]

    ams_opts_dict = {
      "ams": self.get_setting("sim.xcelium.ams"),
      "disciplines": extralib_dict["disciplines"],
      #"disciplines": self.name_finder("disciplines", extralibs),
      "amsconnrules": extralib_dict["amsconnrules"],
      "gen_amscf": extralib_dict["gen_amscf"]
    }

    ams_addt_opts = extralib_dict["ams_addt_opts"]

    filepath_blacklist = extralib_dict["filepath_blacklist"] + [extralib_dict["amscf_template"]]

    self.scriptwriter(options=ams_opts_dict, additional_options=ams_addt_opts, collect=True, sourcedir="src/", blacklist=filepath_blacklist)
    
    # Extract digital-only options from compile, elab, and sim argfiles
    combined_opts = self.option_extractor(["xrun_compile.arg", "xrun_elab.arg", "xrun_sim.arg"])


    self.update_submit_options()
    self.run_executable([self.xcelium_bin, './run_mxh'], cwd=self.run_dir)
    return True
tool = xcelium
