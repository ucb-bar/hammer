# OpenROAD-flow par plugin for Hammer
#
# See LICENSE for licence details.

# NOTE: any hard-coded values are from OpenROAD example flow

import os
import shutil
import errno
import platform
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Callable
from decimal import Decimal
from pathlib import Path
from textwrap import dedent
import importlib.resources

from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict, optional_map
from hammer.vlsi import HammerTool, HammerPlaceAndRouteTool, HammerToolStep, HammerToolHookAction, MMMCCornerType, PlacementConstraintType, TCLTool
from hammer.vlsi.units import TimeValue, CapacitanceValue
from hammer.vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer.vlsi.vendor import OpenROADTool, OpenROADPlaceAndRouteTool

import hammer.tech as hammer_tech
from hammer.tech import RoutingDirection, Site
import hammer.tech.specialcells as specialcells
from hammer.tech.specialcells import CellType, SpecialCell

class OpenROADPlaceAndRoute(OpenROADPlaceAndRouteTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            # FLOORPLAN
            self.floorplan_design,
            self.place_bumps,
            self.macro_placement,
            self.place_tapcells,
            self.power_straps,
            # PLACE
            self.initial_global_placement,
            self.io_placement,
            self.global_placement,
            self.resize,
            self.detailed_placement,
            # CTS
            self.clock_tree,
            self.add_fillers,
            # ROUTING
            self.global_route,
            self.detailed_route,
            # FINISHING
            self.extraction,
            self.write_design,
        ])

    def get_tool_hooks(self) -> List[HammerToolHookAction]:
        return [self.make_persistent_hook(openroad_global_settings)]

    @property
    def _step_transitions(self) -> List[Tuple[str, str]]:
        """
        Private helper property to keep track of which steps we ran so that we
        can create symlinks.
        This is a list of (pre, post) steps
        """
        return self.attr_getter("__step_transitions", [])

    @_step_transitions.setter
    def _step_transitions(self, value: List[Tuple[str, str]]) -> None:
        self.attr_setter("__step_transitions", value)

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        self.created_archive = False
        if self.create_archive_mode  == "latest_run":
            # since OpenROAD won't be run, get OpenROAD "output" from previous run's log
            if not os.path.exists(self.openroad_log):
                self.logger.error("""ERROR: OpenROAD place-and-route must be run before creating an archive. To fix this error:
        1. In your YAML configs, set par.openroad.create_archive_mode : none
        2. Re-run the previous command
        3. Set par.openroad.create_archive_mode : latest_run""")
                exit(1)
            self.logger.warning("Skipping place-and-route run and creating an archive of the latest OpenROAD place-and-route run (because par.openroad.create_archive_mode key was set to 'latest_run')")
            # NOTE: openroad log will be empty if OpenROAD was terminated (e.g. by Ctrl-C)
            with open(self.openroad_log,'r') as f:
                output = f.read()
            self.create_archive(output,0)  # give it a zero exit code to indicate OpenROAD didn't error before this
            exit(0)
        assert super().do_pre_steps(first_step)
        # Restore from the last checkpoint if we're not starting over.
        if first_step != self.first_step:
            self.read_lef()
            self.append(self.read_liberty())
            self.append("read_db pre_{step}".format(step=first_step.name))
            self.read_sdc()
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.verbose_append("write_db pre_{step}".format(step=next.name))
        # Symlink the database to latest for open_chip script later.
        self.append("exec ln -sfn pre_{step} latest".format(step=next.name))
        self._step_transitions = self._step_transitions + [(prev.name, next.name)]
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        # Create symlinks for post_<step> to pre_<step+1> to improve usability.
        try:
            for prev, next in self._step_transitions:
                os.symlink(
                    os.path.join(self.run_dir, "pre_{next}".format(next=next)), # src
                    os.path.join(self.run_dir, "post_{prev}".format(prev=prev)) # dst
                )
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.logger.warning("Failed to create post_* symlinks: " + str(e))

        # Create db post_<last step>
        # TODO: this doesn't work if you're only running the very last step
        if len(self._step_transitions) > 0:
            last = "post_{step}".format(step=self._step_transitions[-1][1])
            self.verbose_append("write_db {last}".format(last=last))
            # Symlink the database to latest for open_chip script later.
            self.verbose_append("exec ln -sfn {last} latest".format(last=last))

        return self.run_openroad()

    @property
    def all_regs_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_paths.json")

    @property
    def all_cells_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_cells.json")

    @property
    def output_sdf_path(self) -> str:
        return os.path.join(self.run_dir, "{top}.par.sdf".format(top=self.top_module))

    @property
    def output_spef_paths(self) -> str:
        return os.path.join(self.run_dir, "{top}.par.spef".format(top=self.top_module))

    @property
    def route_guide_path(self) -> str:
        return os.path.join(self.run_dir, "{top}.route_guide".format(top=self.top_module))

    @property
    def env_vars(self) -> Dict[str, str]:
        v = dict(super().env_vars)
        v["OPENROAD_BIN"] = self.get_setting("par.openroad.openroad_bin")
        return v

    @property
    def output_def_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}.def".format(top=self.top_module))

    @property
    def output_gds_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}.gds".format(top=self.top_module))

    @property
    def output_netlist_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}.lvs.v".format(top=self.top_module))

    @property
    def output_sim_netlist_filename(self) -> str:
        return os.path.join(self.run_dir, "{top}.sim.v".format(top=self.top_module))

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def open_chip_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "open_chip")

    @property
    def open_chip_tcl(self) -> str:
        return self.open_chip_script + ".tcl"

    @property
    def openroad_log(self) -> str:
        return os.path.join(self.run_dir,"openroad.log")

    @property
    def create_archive_mode(self) -> str:
        return self.get_setting("par.openroad.create_archive_mode")

    def tech_lib_filter(self) -> List[Callable[[hammer_tech.Library], bool]]:
        """ Filter only libraries from tech plugin """
        return [self.filter_for_tech_libs]

    def filter_for_tech_libs(self, lib: hammer_tech.Library) -> bool:
        return lib in self.technology.tech_defined_libraries

    def extra_lib_filter(self) -> List[Callable[[hammer_tech.Library], bool]]:
        """ Filter only libraries from vlsi.inputs.extra_libraries """
        return [self.filter_for_extra_libs]

    def filter_for_extra_libs(self, lib: hammer_tech.Library) -> bool:
        return lib in list(map(lambda el: el.store_into_library(), self.technology.get_extra_libraries()))

    @property
    def fill_cells(self) -> str:
        stdfillers = self.technology.get_special_cell_by_type(CellType.StdFiller)
        return ' '.join(list(map(lambda c: str(c), stdfillers[0].name)))


    def fill_outputs(self) -> bool:
        # TODO: no support for ILM
        self.output_ilms = []

        self.output_gds = ""
        self.output_netlist = ""
        self.output_sim_netlist = ""

        if os.path.isfile(self.output_gds_filename):
            self.output_gds = self.output_gds_filename
        if os.path.isfile(self.output_netlist_filename):
            self.output_netlist = self.output_netlist_filename
        if os.path.isfile(self.output_sim_netlist_filename):
            self.output_sim_netlist = self.output_sim_netlist_filename

        # TODO: support outputting the following
        self.hcells_list = []
        self.output_all_regs = ""
        self.output_seq_cells = ""
        self.sdf_file = ""

        return True

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["par.outputs.seq_cells"] = self.output_seq_cells
        outputs["par.outputs.all_regs"] = self.output_all_regs
        outputs["par.outputs.sdf_file"] = self.sdf_file
        return outputs

    def tool_config_prefix(self) -> str:
        return "par.openroad"


    def handle_errors(self, output: str, code: int) -> bool:
        self.logger.error(f"ERROR: OpenROAD returned with a nonzero exit code: {code}.")
        if self.create_archive_mode in ['after_error','always']:
            self.create_archive(output, code)
        else:
            self.logger.info("""To create a tar archive of the issue, set:
            par.openroad.create_archive_mode: latest_run
        in your YAML configs and re-run your par command""")
        return True

    def create_archive(self, output: str, code: int) -> bool:
        """
        Package a tarball of the design for submission to OpenROAD developers.
        Based on the make <design>_issue target in OpenROAD-flow-scripts/flow/util/utils.mk
        output: the entire log output of the OpenROAD run
        code: exit code from OpenROAD
        TODOs:
        - Split par.tcl into constituent steps, conditional filter out everything after floorplan
        - Conditional copy/sourcing of LEFs & LIBs
        - Conditional copy of .pdn file
        """
        self.created_archive = True

        self.logger.error("Generating a tar.gz archive of build/par-rundir to reproduce these results.")

        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        tag = f"{self.top_module}_{platform.platform()}_{now}"
        issue_dir = os.path.join(self.run_dir, tag)
        os.mkdir(issue_dir)

        # Dump the log
        with open(os.path.join(issue_dir, f"{self.top_module}.log"),'w') as f:
            f.write(output)

        # runme script
        runme = os.path.join(issue_dir, "runme.sh")
        with open(runme,'w') as f:
            f.write(dedent("""\
                #!/bin/bash
                openroad -no_init -exit par.tcl"""))
        os.chmod(runme, 0o755) # +x

        # Gather files in self.run_dir
        file_exts = [".tcl", ".sdc", ".pdn", ".lef"]
        for match in list(filter(lambda x: any(ext in x for ext in file_exts), os.listdir(self.run_dir))):
            src = os.path.join(self.run_dir, match)
            dest = os.path.join(issue_dir, match)
            self.logger.info(f"Copying: {src} -> {dest}")
            shutil.copy2(src, dest)
        self.logger.info(f"Done with copying files with these extensions: {file_exts}")

        # Verilog
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        for verilog_file in abspath_input_files:
            shutil.copy2(verilog_file, os.path.join(issue_dir, os.path.basename(verilog_file)))

        # LEF
        # This will also copy LEF files that were then hacked in read_lef() but already copied above
        lef_files = self.technology.read_libs([
            hammer_tech.filters.lef_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_lefs = list(map(lambda ilm: ilm.lef, self.get_input_ilms()))
            lef_files.extend(ilm_lefs)
        for lef_file in lef_files:
            shutil.copy2(lef_file, os.path.join(issue_dir, os.path.basename(lef_file)))

        # LIB
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        for corner in corners:
            for lib_file in self.get_timing_libs(corner).split():
                shutil.copy2(lib_file, os.path.join(issue_dir, os.path.basename(lib_file)))

        # Hack par.tcl script
        # Remove abspaths to files since they are now in issue_dir
        subprocess.call(["sed", "-i", "s/\(.* \)\(.*\/\)\(.*\)/\\1\\3/g", os.path.join(issue_dir, "par.tcl")])
        # Comment out exec klayout block
        subprocess.call(["sed", "-i", "s/\(exec klayout\|-rd\|-rm\)/# \\1/g", os.path.join(issue_dir, "par.tcl")])

        # Tar up the directory, delete it
        subprocess.call(["tar",
                        "-C", os.path.relpath(self.run_dir),
                        "-zcf", f"{tag}.tar.gz", tag])
        shutil.rmtree(issue_dir)

        if self.create_archive_mode == 'always':
            self.logger.info("To disable archive creation after each OpenROAD run, remove the par.openroad.create_archive_mode key from your YAML configs (or set it to 'none' or 'after_error')")
        if self.create_archive_mode == 'after_error':
            self.logger.info("To disable archive creation after each OpenROAD error, add this to your YAML config: \n\tpar.openroad.create_archive_mode: none")
        self.logger.error(f"Place-and-route run was archived to: {tag}.tar.gz")

        return True

    def gui(self) -> str:
        cmds=[]
        cmds.append(self.read_liberty())
        cmds.append("read_db latest")
        return '\n'.join(cmds)

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_openroad(self) -> bool:
        # Quit OpenROAD.
        self.append("exit")

        # Create par script.
        par_tcl_filename = os.path.join(self.run_dir, "par.tcl")
        with open(par_tcl_filename, "w") as f:
            f.write("\n".join(self.output))

        # Create open_chip script pointing to latest (symlinked to post_<last ran step>).
        with open(self.open_chip_tcl, "w") as f:
            f.write(self.gui())

        with open(self.open_chip_script, "w") as f:
            f.write("""#!/bin/bash
        cd {run_dir}
        source enter
        $OPENROAD_BIN -no_init -gui {open_chip_tcl}
                """.format(run_dir=self.run_dir, open_chip_tcl=self.open_chip_tcl))
        os.chmod(self.open_chip_script, 0o755)

        num_threads = str(self.get_setting("vlsi.core.max_threads"))

        # Build args.
        args = [
            self.get_setting("par.openroad.openroad_bin"),
            "-no_init",             # do not read .openroad init file
            "-log", self.openroad_log,
            "-threads", num_threads,
            "-exit",                # exit after reading par_tcl_filename
            par_tcl_filename
        ]
        if bool(self.get_setting("par.openroad.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + " ".join(args))
        else:
            output = self.run_executable(args, cwd=self.run_dir)
            if not self.created_archive and self.create_archive_mode  == "always":
                self.create_archive(output,0)  # give it a zero exit code to indicate OpenROAD didn't error before this
        return True

    def get_timing_libs(self, corner: Optional[MMMCCorner] = None) -> str:
        """
        Helper function to get the list of ASCII timing .lib files in space separated format.
        Note that Cadence tools support ECSM, so we can use the ECSM-based filter.

        :param corner: Optional corner to consider. If supplied, this will use filter_for_mmmc to select libraries that
        match a given corner (voltage/temperature).
        :return: List of lib files separated by spaces
        """
        pre_filters = optional_map(corner, lambda c: [self.filter_for_mmmc(voltage=c.voltage,temp=c.temp)])  # type: Optional[List[Callable[[hammer_tech.Library],bool]]]
        lib_args = self.technology.read_libs([hammer_tech.filters.timing_lib_with_ecsm_filter], hammer_tech.HammerTechnologyUtils.to_plain_item, extra_pre_filters=pre_filters)
        return " ".join(lib_args)

    def read_lef(self) -> bool:
        # OpenROAD names the LEF libraries by filename:
        #   foo.tlef and foo.lef evaluate to the same library "foo"
        #   solution: copy foo.lef to foo1.lef
        lef_files = self.technology.read_libs([
            hammer_tech.filters.lef_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_lefs = list(map(lambda ilm: ilm.lef, self.get_input_ilms()))
            lef_files.extend(ilm_lefs)
        lef_file_libnames=[]
        unique_id=0
        for lef_file in lef_files:
            lef_file_name=lef_file.split('/')[-1]
            lef_file_libname=''.join(lef_file_name.split('.')[:-1])
            lef_file_ext=lef_file_name.split('.')[-1]
            if lef_file_libname in lef_file_libnames:
                lef_file_libname=f"{lef_file_libname}_{unique_id}.{lef_file_ext}"
                new_lef_file=f"{self.run_dir}/{lef_file_libname}"
                shutil.copyfile(lef_file, new_lef_file)
                unique_id+=1
                lef_file_libnames.append(lef_file_libname)
                lef_file = new_lef_file
            self.append(f"read_lef {lef_file}")
        self.append("")
        return True

    def read_liberty(self) -> str:
        cmds=[]
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        if corners:
            corner_names = []
            for corner in corners:
                # Setting up views for all defined corner types: setup, hold, extra
                if corner.type is MMMCCornerType.Setup:
                    corner_name="setup"
                elif corner.type is MMMCCornerType.Hold:
                    corner_name="hold"
                elif corner.type is MMMCCornerType.Extra:
                    corner_name="extra"
                else:
                    raise ValueError("Unsupported MMMCCornerType")
                corner_names.append(corner_name)

            cmds.append(f"define_corners {' '.join(corner_names)}")
            for corner,corner_name in zip(corners,corner_names):
                lib_files=self.get_timing_libs(corner)
                for lib_file in lib_files.split():
                    cmds.append(f"read_liberty -corner {corner_name} {lib_file}")
        cmds.append("")
        return '\n'.join(cmds)

    def scale_units_1000x_down(self,prefix) -> str:
        # convert SI prefix down by 1000x
        if prefix == 'a':
            return 'f'
        if prefix == 'f':
            return 'p'
        if prefix == 'p':
            return 'n'
        if prefix == 'n':
            return 'u'
        if prefix == 'u':
            return 'm'
        if prefix == 'm':
            return ''
        return ''

    def read_sdc(self) -> bool:
        # overwrite SDC file to exclude group_path command
        # change units in SDC file (1000.0fF and 1000.0ps cause errors)

        sdc_files = self.generate_sdc_files()
        for sdc_file in sdc_files[:-1]:
            self.append(f"read_sdc -echo {sdc_file}")

        return True

    #========================================================================
    # par main steps
    #========================================================================
    def init_design(self) -> bool:
        # set up useful variables
        clock_port = self.get_clock_ports()[0]
        self.clock_port_name = clock_port.name

        # start routine
        self.read_lef()
        self.append(self.read_liberty())

        # read_verilog
        # We are switching working directories and we still need to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        for verilog_file in abspath_input_files:
            self.append(f"read_verilog {verilog_file}")
        self.append(f"link_design {self.top_module}\n")
        self.read_sdc()
        return True

    def floorplan_design(self) -> bool:

        floorplan_tcl = os.path.join(self.run_dir, "floorplan.tcl")
        with open(floorplan_tcl, "w") as f:
            f.write("\n".join(self.create_floorplan_tcl()))

        self.block_append(f"""
        ################################################################
        # Floorplan Design

        # Init floorplan + Place Macros
        source -verbose {floorplan_tcl}

        # Make tracks
        # create routing tracks""")
        self.append(self.generate_make_tracks_tcl())
        self.block_append(f"""

        # remove buffers inserted by synthesis
        remove_buffers

        # IO Placement (random)
        {self.place_pins_tcl(random=True)}

        """)

        return True


    def place_bumps(self) -> bool:
        # placeholder for tutorials
        return True


    def macro_placement(self) -> bool:
        floorplan_mode = str(self.get_setting("par.openroad.floorplan_mode"))
        if floorplan_mode == 'auto':
            # TODO: did I understand the par.blockage_spacing key correctly?
            spacing = self.get_setting("par.blockage_spacing")

            self.block_append(r"""
            ################################################################
            # Auto Macro Placement (for any unplaced macros)

            proc find_macros {} {
                set macros ""
                set block [[[ord::get_db] getChip] getBlock]
                foreach inst [$block getInsts] {
                    set inst_master [$inst getMaster]
                    # BLOCK means MACRO cells
                    if { [string match [$inst_master getType] "BLOCK"] } {
                        append macros " " $inst
                    }
                }
                return $macros
            }
            """, verbose=False)
            self.block_append(f"""
            if {{[find_macros] != ""}} {{
                # Timing Driven Mixed Sized Placement
                global_placement -density 0.6 -pad_left 1 -pad_right 1
                # ParquetFP-based macro cell placer, “TritonMacroPlacer”
                macro_placement -halo "{spacing} {spacing}" -channel "{2*spacing} {2*spacing}"
            }}
            """)
        return True


    def place_tapcells(self) -> bool:
        tap_cells = self.technology.get_special_cell_by_type(CellType.TapCell)
        endcap_cells = self.technology.get_special_cell_by_type(CellType.EndCap)
        if len(tap_cells) == 0:
            self.logger.warning("Tap cells are improperly defined in the tech plugin and will not be added. This step should be overridden with a user hook.")
            return True
        endcap_arg = ""
        if len(endcap_cells) == 0:
            self.logger.warning("Endcap cells are improperly defined in the tech plugin and will not be added.")
        else:
            endcap_arg = "-endcap_master " + str(endcap_cells[0].name[0])
        tap_cell = tap_cells[0].name[0]
        try:
            interval = self.get_setting("vlsi.technology.tap_cell_interval")
            offset = self.get_setting("vlsi.technology.tap_cell_offset")
            self.block_append(f"""
            ################################################################
            # Tapcell insertion
            tapcell -tapcell_master {tap_cell} {endcap_arg} -distance {interval} -halo_width_x {offset} -halo_width_y {offset}
            """)
        except KeyError:
            pass
        finally:
            self.logger.warning(
                "You have not overridden place_tap_cells. By default this step adds a simple set of tapcells or does nothing; you will have trouble with power strap creation later.")
        return True

    def generate_pdn_config(self, pdn_config_path) -> bool:

        pwr_nets=self.get_all_power_nets()
        gnd_nets=self.get_all_ground_nets()
        primary_pwr_net=pwr_nets[0].name
        primary_gnd_net=gnd_nets[0].name
        all_metal_layer_names = [layer.name for layer in self.get_stackup().metals]

        strap_layers = self.get_setting("par.generate_power_straps_options.by_tracks.strap_layers").copy()
        std_cell_rail_layer_name = str(self.get_setting("technology.core.std_cell_rail_layer"))
        std_cell_rail_layer = self.get_stackup().get_metal(std_cell_rail_layer_name)
        std_cell_rail_minwidth = std_cell_rail_layer.min_width

        # std_cell_rail_layer_minwidth =
        strap_layers.insert(0,std_cell_rail_layer_name)
        top_strap_layer = strap_layers[-1]
        straps = '\n    '.join(self.create_power_straps_tcl())

        metal_pairs=" "
        for i in range(0,len(strap_layers)-1):
            metal_pairs+=f"{{{strap_layers[i]} {strap_layers[i+1]}}} "

        global_connections_pwr=""
        for pwr_net in pwr_nets:
            if pwr_net.tie is not None:
                global_connections_pwr += f"\n    {{inst_name .* pin_name {pwr_net.name}}}"

        global_connections_gnd=""
        for gnd_net in gnd_nets:
            if gnd_net.tie is not None:
                global_connections_gnd += f"\n    {{inst_name .* pin_name {gnd_net.name}}}"

        # blockages
        top_blockage_layer = self.get_setting("par.blockage_spacing_top_layer")
        top_blockage_layer_idx = all_metal_layer_names.index(top_blockage_layer)
        blockage_layers = all_metal_layer_names[:top_blockage_layer_idx+1]

        pdn_cfg=f"""\
# Floorplan information - core boundary coordinates, std. cell row height,
# minimum track pitch as defined in LEF


# POWER or GROUND #Std. cell rails starting with power or ground rails at the bottom of the core area
set ::rails_start_with "POWER" ;

# POWER or GROUND #Upper metal stripes starting with power or ground rails at the left/bottom of the core area
set ::stripes_start_with "POWER" ;

# Power nets
set ::power_nets  "{primary_pwr_net}"
set ::ground_nets "{primary_gnd_net}"

set pdngen::global_connections {{
  {primary_pwr_net} {{    {global_connections_pwr}
  }}
  {primary_gnd_net} {{    {global_connections_gnd}
  }}
}}
##===> Power grid strategy
# Ensure pitches and offsets will make the stripes fall on track

pdngen::specify_grid stdcell {{
  name grid
  rails {{
    {std_cell_rail_layer_name} {{width {std_cell_rail_minwidth} offset 0}}
  }}
  straps {{
    {straps}
  }}
  connect {{{metal_pairs}}}
}}

pdngen::specify_grid macro {{
  orient {{R0 R180 MX MY}}
  power_pins  "{' '.join(self.get_setting("technology.core.std_cell_supplies.power"))}"
  ground_pins "{' '.join(self.get_setting("technology.core.std_cell_supplies.ground"))}"
  blockages "{" ".join(blockage_layers)}"
  connect {{{{{top_blockage_layer}_PIN_ver {top_strap_layer}}}}}
}}

# Need a different strategy for rotated rams to connect to rotated pins
# No clear way to do this for a 5 metal layer process
pdngen::specify_grid macro {{
    orient {{R90 R270 MXR90 MYR90}}
    power_pins "{' '.join(self.get_setting("technology.core.std_cell_supplies.power"))}"
    ground_pins "{' '.join(self.get_setting("technology.core.std_cell_supplies.ground"))}"
    blockages "{" ".join(blockage_layers)}"
    connect {{{{{top_blockage_layer}_PIN_hor {top_strap_layer}}}}}
}}
"""

        with open(pdn_config_path, "w") as f:
            f.write(pdn_cfg)

        return True

    def power_straps(self) -> bool:
        """Place the power straps for the design."""
        power_straps_tcl_path = os.path.join(self.run_dir, "power_straps.pdn")
        # power_straps_tcl_path = os.path.join(self.run_dir, "power_straps.tcl")
        self.generate_pdn_config(power_straps_tcl_path)
        self.block_append(f"""
        ################################################################
        # Power distribution network insertion
        pdngen -verbose {power_straps_tcl_path}
        """)
        return True

    def initial_global_placement(self) -> bool:
        metals=self.get_stackup().metals[1:]
        spacing = self.get_setting("par.blockage_spacing")
        idx_clock_bottom_metal=min(2,len(metals)-1)

        self.block_append(f"""
        ################################################################
        # Global placement (without placed IOs, timing-driven, and routability-driven)
        global_placement -overflow 0.2 -density 0.6 -pad_left 4 -pad_right 4
        """)
        return True


    def place_pins_tcl(self,random=False) -> str:
        random_arg=""
        if random: random_arg="-random"

        stackup = self.get_stackup()
        all_metal_layer_names = [layer.name for layer in self.get_stackup().metals]
        pin_assignments = self.get_pin_assignments()
        hor_layers=[]
        ver_layers=[]
        for pin in pin_assignments:
            if pin.layers is not None and len(pin.layers) > 0:
                for pin_layer_name in pin.layers:
                    layer = self.get_stackup().get_metal(pin_layer_name)
                    if layer.direction==RoutingDirection.Horizontal:
                        hor_layers.append(pin_layer_name)
                    if layer.direction==RoutingDirection.Vertical:
                        ver_layers.append(pin_layer_name)

        # both hor_layers and ver_layers arguments are required
        # if missing, auto-choose one or both
        # TODO: Hammer currently throws an error if both horizontal + vertical pin layers are specified
        if not (hor_layers and ver_layers):
            self.logger.warning("Both horizontal and vertical pin layers should be specified. Hammer will auto-specify one or both.")
            # choose first pin layer to be middle of stackup
            #   or use pin layer in either hor_layers or ver_layers
            pin_layer_names=["",""]
            pin_layer_names[0]=all_metal_layer_names[int(len(all_metal_layer_names)/2)]
            if (hor_layers): pin_layer_names[0]=hor_layers[0]
            if (ver_layers): pin_layer_names[0]=ver_layers[0]
            pin_layer_idx_1=all_metal_layer_names.index(pin_layer_names[0])
            if (pin_layer_idx_1 < len(all_metal_layer_names)-1):
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1+1]
            elif (pin_layer_idx_1 > 0):
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1-1]
            else: # edge-case
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1]
            for pin_layer_name in pin_layer_names:
                layer = self.get_stackup().get_metal(pin_layer_name)
                if (layer.direction==RoutingDirection.Horizontal) and (pin_layer_name not in hor_layers):
                    hor_layers.append(pin_layer_name)
                if (layer.direction==RoutingDirection.Vertical)   and (pin_layer_name not in ver_layers):
                    ver_layers.append(pin_layer_name)
        # determine commands for side specified in pin assignments
        #   can only be done in openroad by "excluding" the entire length of the other 3 sides from pin placement
        side=""
        for pin in pin_assignments:
            if pin.side == "bottom":
                side="-exclude top:* -exclude right:* -exclude left:*"
            elif pin.side == "top":
                side="-exclude bottom:* -exclude right:* -exclude left:*"
            elif pin.side == "left":
                side="-exclude top:* -exclude right:* -exclude bottom:*"
            elif pin.side == "right":
                side="-exclude top:* -exclude bottom:* -exclude left:*"

        return f"place_pins {random_arg} -hor_layers {{{' '.join(hor_layers)}}} -ver_layers {{{' '.join(ver_layers)}}} {side}"

    def io_placement(self) -> bool:
        self.block_append(f"""
        ################################################################
        # IO Placement
        {self.place_pins_tcl()}
        """)
        return True


    def global_placement(self) -> bool:
        metals=self.get_stackup().metals[1:]
        spacing = self.get_setting("par.blockage_spacing")
        idx_clock_bottom_metal=min(2,len(metals)-1)

        self.block_append(f"""
        ################################################################
        # Global placement (with placed IOs, timing-driven, and routability-driven)
        set_dont_use {{{' '.join(self.get_dont_use_list())}}}
        set_global_routing_layer_adjustment {metals[0].name}-{metals[-1].name} 0.3
        set_routing_layers -signal {metals[0].name}-{metals[-1].name} -clock {metals[idx_clock_bottom_metal].name}-{metals[-1].name}
        # creates blockages around macros
        # set_macro_extension 2

        # -density default is 0.7, overflow default is 0.1
        # set overflow higher (ex. 0.8) to make faster
        global_placement -routability_driven -overflow 0.2 -pad_left 4 -pad_right 4
        # TODO: -routability_driven breaks this!!!

        # estimate_parasitics -placement
        """)

        return True

    def resize(self) -> bool:
        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)
        tie_hilo_cells = self.technology.get_special_cell_by_type(CellType.TieHiLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1:
            self.logger.warning("Hi and Lo tiecells are unspecified or improperly specified and will not be added.")
        elif tie_hi_cells[0].output_ports is None or tie_lo_cells[0].output_ports is None:
            self.logger.warning("Hi and Lo tiecells output ports are unspecified or improperly specified and will not be added.")
        else:
            tie_hi_cell = tie_hi_cells[0].name[0]
            tie_hi_port = tie_hi_cells[0].output_ports[0]
            tie_lo_cell = tie_lo_cells[0].name[0]
            tie_lo_port = tie_lo_cells[0].output_ports[0]

        self.block_append(f"""
        ################################################################
        # Resizing & Buffering
        estimate_parasitics -placement
        repair_design -slew_margin 0 -cap_margin 0

        # Repair tie lo/hi fanout
        set tielo_lib_name [get_name [get_property [lindex [get_lib_cell {tie_lo_cell}] 0] library]]
        set tiehi_lib_name [get_name [get_property [lindex [get_lib_cell {tie_hi_cell}] 0] library]]
        repair_tie_fanout -separation 0 $tielo_lib_name/{tie_lo_cell}/{tie_lo_port}
        repair_tie_fanout -separation 0 $tiehi_lib_name/{tie_hi_cell}/{tie_hi_port}
        """)
        return True


    def detailed_placement(self) -> bool:
        self.block_append(f"""
        ################################################################
        # Detail placement

        # default detail_place_pad value in OpenROAD = 2
        set_placement_padding -global -left 0 -right 0
        detailed_placement

        # improve_placement
        optimize_mirroring

        """)
        return True

    def check_detailed_placement(self) -> bool:
        """
        for any step that runs the detailed_placement command,
            run this function at the start of the NEXT step
            so that the post-step database is saved and in the case of a check_placement error,
            the database it may be opened in the OpenROAD gui for debugging the error
        """
        self.block_append(f"""
        check_placement -verbose

        # post resize timing report (ideal clocks)
        report_worst_slack -min -digits 3
        report_worst_slack -max -digits 3
        report_tns -digits 3

        # Check slew repair
        report_check_types -max_slew -max_capacitance -max_fanout -violators

        """)
        return True

    def clock_tree(self) -> bool:
        self.check_detailed_placement()
        clock_port = self.get_clock_ports()[0]
        self.clock_port_name = clock_port.name

        cts_buffer_cells = self.technology.get_special_cell_by_type(CellType.CTSBuffer)

        cts_args=""
        if cts_buffer_cells is None:
            self.logger.warning("CTS buffer cells are unspecified.")
        else:
            cts_buffer_cell = cts_buffer_cells[0].name[0]
            cts_args=f"-root_buf {cts_buffer_cell} -buf_list {cts_buffer_cell}"

        self.block_append(f"""
        ################################################################
        # Clock Tree Synthesis
        # Run TritonCTS
        repair_clock_inverters

        set_placement_padding -global -left 2 -right 2

        repair_clock_inverters
        clock_tree_synthesis {cts_args} -sink_clustering_enable \\
                                        -sink_clustering_size 30 \\
                                        -sink_clustering_max_diameter 100

        set_propagated_clock [all_clocks]

        # CTS leaves a long wire from the pad to the clock tree root.
        repair_clock_nets

        # place clock buffers
        detailed_placement

        ###########################
        # Setup/hold timing repair

        set_placement_padding -global -left 0 -right 0

        set_propagated_clock [all_clocks]

        # -placement|-global_routing
        estimate_parasitics -placement

        repair_timing -setup

        repair_timing -hold

        detailed_placement
        """)
        return True


    def add_fillers(self) -> bool:
        self.check_detailed_placement()
        """add decap and filler cells"""
        self.block_append(f"""
        ################################################################
        # Filler cell insertion
        # optimize_mirroring - tries to reduce wirelength
        # Capture utilization before fillers make it 100%
        utl::metric "utilization" [format %.1f [expr [rsz::utilization] * 100]]
        utl::metric "design_area" [sta::format_area [rsz::design_area] 0]

        filler_placement {{ {self.fill_cells} }}
        """)
        return True


    def global_route(self) -> bool:
        self.check_detailed_placement()
        metals=self.get_stackup().metals[1:]

        self.block_append(f"""
        ################################################################
        # Global routing
        set_global_routing_layer_adjustment {metals[0].name}-{metals[-1].name} 0.7
        set_routing_layers -signal {metals[0].name}-{metals[-1].name} -clock met3-met5
        # hard-coded in the example OpenROAD scripts
        # set_macro_extension 2

        # pin_access - this command caused openroad to crash
        # -allow_congestion and -allow_overflow added for now

        global_route -allow_congestion -congestion_iterations 200 -verbose \\
                     -guide_file {self.route_guide_path}

        set_propagated_clock [all_clocks]
        estimate_parasitics -global_routing

        check_antennas -report_file {self.run_dir}/antenna.log -report_violating_nets
        """)
        return True


    def detailed_route(self) -> bool:
        metals=self.get_stackup().metals[1:]

        self.block_append(f"""
        ################################################################
        # Detailed routing

        set_thread_count {self.get_setting("vlsi.core.max_threads")}

        # NOTE: many other arguments available
        detailed_route -guide {self.route_guide_path} \\
            -bottom_routing_layer {metals[0].name} \\
            -top_routing_layer {metals[-1].name} \\
            -output_guide {self.run_dir}/{self.top_module}_output_guide.mod \\
            -output_drc {self.run_dir}/{self.top_module}_route_drc.rpt \\
            -output_maze {self.run_dir}/{self.top_module}_maze.log \\
            -verbose 1
        """)
        return True


    def extraction(self) -> bool:
        sed_expr=r"{s/\\//g}"  # use sed find+replace to remove '\' character
        self.block_append(f"""
        ################################################################
        # Extraction
        define_process_corner -ext_model_index 0 X

        extract_parasitics -ext_model_file {self.get_setting("par.openroad.openrcx_techfile")}

        # touch the file in case write_spef fails
        exec touch {self.output_spef_paths}
        write_spef {self.output_spef_paths}
        # remove backslashes in instances so that read_spef recognizes the instances
        exec sed -i {sed_expr} {self.output_spef_paths}

        read_spef {self.output_spef_paths}
        """)
        # alternative: use global routing based parasitics inlieu of rc extraction
        #   >> estimate_parasitics -global_routing
        return True


    # Copy and hack the klayout techfile, to add all required LEFs
    def setup_klayout_techfile(self) -> bool:
        source_path = Path(self.get_setting("par.openroad.klayout_techfile_source"))
        klayout_techfile_filename = os.path.basename(source_path)
        if not source_path.exists():
            self.logger.error("Klayout techfiles not specified in tech plugin. Klayout won't be able to write GDS file.")
            return False
            # raise FileNotFoundError(f"Klayout techfile not found: {source_path}")

        cache_tech_dir_path = Path(self.technology.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / klayout_techfile_filename
        self.klayout_techfile_path = dest_path

        # klayout needs all lefs
        tech_lib_lefs = self.technology.read_libs([hammer_tech.filters.lef_filter], hammer_tech.HammerTechnologyUtils.to_plain_item, self.tech_lib_filter())
        # tech_lef = tech_lib_lefs[0]
        extra_lib_lefs = self.technology.read_libs([hammer_tech.filters.lef_filter], hammer_tech.HammerTechnologyUtils.to_plain_item, self.extra_lib_filter())

        insert_lines=''
        for lef_file in tech_lib_lefs+extra_lib_lefs:
            insert_lines += f"<lef-files>{lef_file}</lef-files>\n"

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying Klayout Techfile: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    if '</lefdef>' in line:
                        df.write(insert_lines)
                    df.write(line)
        return True


    def write_gds(self) -> bool:
        self.setup_klayout_techfile()

        gds_files = self.technology.read_libs([
            hammer_tech.filters.gds_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_gds = list(map(lambda ilm: ilm.gds, self.get_input_ilms()))
            gds_files.extend(ilm_gds)

        def2stream_text = importlib.resources.files("hammer.vlsi.vendor").joinpath("def2stream.py").read_text()
        def2stream_path = Path(self.technology.cache_dir) / "def2stream.py"
        def2stream_path.write_text(def2stream_text)
        self.block_append(f"""
        # write gds
        exec klayout -zz \\
                -rd design_name={self.top_module} \\
                -rd in_def={self.output_def_filename} \\
                -rd in_files={" ".join(gds_files)} \\
                -rd seal_file= \\
                -rd tech_file={self.klayout_techfile_path} \\
                -rd config_file= \\
                -rd out_file={self.output_gds_filename} \\
                -rm {str(def2stream_path)}
        """)
        return True


    def write_sdf(self) -> bool:
        corners = self.get_mmmc_corners()
        self.append(f"write_sdf -corner setup {self.output_sdf_path}")
        return True


    def write_spefs(self) -> bool:

        return True


    def write_regs(self) -> bool:
        # TODO: currently no analagous OpenROAD default script
        return True


    def write_reports(self) -> bool:
        # TODO: write all these to report files
        self.block_append("""
        ################################################################
        # Final Report
        report_checks -path_delay min_max -format full_clock_expanded -fields {input_pin slew capacitance} -digits 3
        report_worst_slack -min -digits 3
        report_worst_slack -max -digits 3
        report_tns -digits 3
        report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3
        report_clock_skew -digits 3
        report_power -corner "hold"

        report_floating_nets -verbose
        report_design_area

        utl::metric "worst_slack_min" [sta::worst_slack -min]
        utl::metric "worst_slack_max" [sta::worst_slack -max]
        utl::metric "tns_max" [sta::total_negative_slack -max]
        utl::metric "clock_skew" [sta::worst_clock_skew -setup]
        utl::metric "max_slew_violations" [sta::max_slew_violation_count]
        utl::metric "max_fanout_violations" [sta::max_fanout_violation_count]
        utl::metric "max_capacitance_violations" [sta::max_capacitance_violation_count]
        # report clock period as a metric for updating limits
        utl::metric "clock_period" [get_property [lindex [all_clocks] 0] period]
        """)
        return True


    def write_design(self) -> bool:
        self.block_append(f"""
        ################################################################
        # Write Design

        # write DEF (need this to write GDS)
        write_def {self.output_def_filename}

        # write netlist
        write_verilog -include_pwr_gnd -remove_cells {{{self.fill_cells}}} {self.output_netlist_filename}
        """)

        # TODO: look at IR drop analysis from ~OpenROAD-flow-scripts/flow/scripts/final_report.tcl
        # Static IR drop analysis

        # GDS streamout.
        self.write_gds()

        # Write SDF
        self.write_sdf()

        # Make sure that generated-scripts exists.
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        self.write_reports()

        self.ran_write_design=True

        return True


    def generate_make_tracks_tcl(self) -> str:
        output = []
        # initialize_floorplan removes existing tracks
        #   --> use the make_tracks command to add routing tracks
        #       to a floorplan (with no arguments it uses default from tech LEF)
        layers = self.get_setting("par.generate_power_straps_options.by_tracks.strap_layers")
        for metal in self.get_stackup().metals:
            # TODO: might need separate x/y pitch definition in stackup
            output.append(f"make_tracks {metal.name} -x_offset {metal.offset} -x_pitch {metal.pitch} -y_offset {metal.offset} -y_pitch {metal.pitch}")
        return "\n".join(output)


    def create_floorplan_tcl(self) -> List[str]:
        """
        Create a floorplan TCL depending on the floorplan mode.
        """
        output = []  # type: List[str]

        floorplan_mode = str(self.get_setting("par.openroad.floorplan_mode"))
        if floorplan_mode == "manual":
            floorplan_script_contents = str(self.get_setting("par.openroad.floorplan_script_contents"))
            output.append("# Floorplan manually specified from HAMMER")
            output.extend(floorplan_script_contents.split("\n"))
        elif floorplan_mode == "generate":
            output.extend(self.generate_floorplan_tcl())
        elif floorplan_mode == "auto":
            spacing = self.get_setting("par.blockage_spacing")
            bot_layer = self.get_stackup().get_metal_by_index(1).name
            top_layer = self.get_setting("par.blockage_spacing_top_layer")
        else:
            if floorplan_mode != "blank":
                self.logger.error("Invalid floorplan_mode {mode}. Using blank floorplan.".format(mode=floorplan_mode))
            # Write blank floorplan
            output.append("# Blank floorplan specified from HAMMER")
        return output

    @staticmethod
    def generate_chip_size_constraint(width: Decimal, height: Decimal, left: Decimal, bottom: Decimal, right: Decimal,
                                      top: Decimal, site: str) -> str:
        """
        Given chip width/height and margins, generate an OpenROAD TCL command to create the floorplan.
        Also requires a technology specific name for the core site
        """
        return f"initialize_floorplan -site {site} -die_area {{ 0 0 {width} {height}}} -core_area {{{left} {bottom} {width-right-left} {height-top-bottom}}}"

    def generate_floorplan_tcl(self) -> List[str]:
        """
        Generate a TCL floorplan for OpenROAD based on the input config/IR.
        Not to be confused with create_floorplan_tcl, which calls this function.
        """
        output = []  # type: List[str]

        # TODO(edwardw): proper source locators/SourceInfo
        output.append("# Floorplan automatically generated from HAMMER")

        # Top-level chip size constraint.
        # Default/fallback constraints if no other constraints are provided.
        # TODO snap this to a core site
        chip_size_constraint = self.generate_chip_size_constraint(
            site=self.technology.get_placement_site().name,
            width=Decimal("1000"), height=Decimal("1000"),
            left=Decimal("100"), bottom=Decimal("100"),
            right=Decimal("100"), top=Decimal("100")
        )

        floorplan_constraints = self.get_placement_constraints()
        global_top_layer = self.get_setting("par.blockage_spacing_top_layer") #  type: Optional[str]

        ############## Actually generate the constraints ################
        for constraint in floorplan_constraints:
            # Floorplan names/insts need to not include the top-level module,
            # despite the internal get_db commands including the top-level module...
            # e.g. Top/foo/bar -> foo/bar
            new_path = "/".join(constraint.path.split("/")[1:])

            if new_path == "":
                assert constraint.type == PlacementConstraintType.TopLevel, "Top must be a top-level/chip size constraint"
                margins = constraint.margins
                assert margins is not None
                # Set top-level chip dimensions.
                chip_size_constraint = self.generate_chip_size_constraint(
                    site=self.technology.get_placement_site().name,
                    width=constraint.width,
                    height=constraint.height,
                    left=margins.left,
                    bottom=margins.bottom,
                    right=margins.right,
                    top=margins.top
                )
            else:
                orientation = constraint.orientation if constraint.orientation is not None else "r0"
                # openroad names orientations differently from hammer
                #   hammer:   r0|r90|r180|r270|mx|my|mx90 |my90
                #   openroad: R0|R90|R180|R270|MX|MY|MXR90|MYR90
                orientation = orientation.upper()
                if constraint.orientation == "mx90":
                    orientation = "MXR90"
                elif constraint.orientation == "my90":
                    orientation = "MYR90"
                if constraint.create_physical:
                    pass
                if constraint.type == PlacementConstraintType.Dummy:
                    pass
                elif constraint.type == PlacementConstraintType.Placement:
                    pass
                # for OpenROAD
                elif constraint.type in [PlacementConstraintType.HardMacro, PlacementConstraintType.Hierarchical]:
                    inst_name=new_path
                    floorplan_cmd = f"place_cell -inst_name {inst_name} -orient {orientation} -origin {{ {constraint.x} {constraint.y} }} -status FIRM"

                    output.append("# only place macro if it is present in design")
                    output.append(f'if {{[[set block [ord::get_db_block]] findInst {inst_name}] == "NULL"}} {{')
                    output.append(f'  puts "(ERROR) Cell/macro {inst_name} not found!"')
                    output.append("} else {")
                    output.append(f'  puts "{floorplan_cmd}"')
                    output.append(f"  {floorplan_cmd}")
                    output.append("}")
                    # TODO: add place_cell option [-status (PLACED|FIRM)]
                    spacing = self.get_setting("par.blockage_spacing")
                    if constraint.top_layer is not None:
                        current_top_layer = constraint.top_layer #  type: Optional[str]
                    elif global_top_layer is not None:
                        current_top_layer = global_top_layer
                    else:
                        current_top_layer = None
                    # TODO: find equivalent for place/route halo in OpenROAD

                elif constraint.type == PlacementConstraintType.Obstruction:
                    pass
                else:
                    assert False, "Should not reach here"
        return [chip_size_constraint] + output

    def specify_power_straps(self, layer_name: str, bottom_via_layer_name: str, blockage_spacing: Decimal, pitch: Decimal, width: Decimal, spacing: Decimal, offset: Decimal, bbox: Optional[List[Decimal]], nets: List[str], add_pins: bool) -> List[str]:
        """
        Generate a list of TCL commands that will create power straps on a given layer.
        This is a low-level, cad-tool-specific API. It is designed to be called by higher-level methods, so calling this directly is not recommended.
        This method assumes that power straps are built bottom-up, starting with standard cell rails.

        :param layer_name: The layer name of the metal on which to create straps.
        :param bottom_via_layer_name: The layer name of the lowest metal layer down to which to drop vias.
        :param blockage_spacing: The minimum spacing between the end of a strap and the beginning of a macro or blockage.
        :param pitch: The pitch between groups of power straps (i.e. from left edge of strap A to the next left edge of strap A).
        :param width: The width of each strap in a group.
        :param spacing: The spacing between straps in a group.
        :param offset: The offset to start the first group.
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power nets to create (e.g. ["VDD", "VSS"], ["VDDA", "VSS", "VDDB"],  ... etc.).
        :param add_pins: True if pins are desired on this layer; False otherwise.
        :return: A list of TCL commands that will generate power straps.
        """
        pdn_cfg = [f" {layer_name} {{width {width} pitch {pitch} offset {offset}}}"]
        tcl = [f"add_pdn_stripe -grid {{grid}} -layer {{{layer_name}}} -width {width} -pitch {pitch} -offset {offset}\n"]
        return pdn_cfg

    def process_sdc_file(self,post_synth_sdc) -> str:
        # overwrite SDC file to exclude group_path command
        # change units in SDC file (1000.0fF and 1000.0ps cause errors)
        sdc_filename=os.path.basename(post_synth_sdc)
        new_post_synth_sdc = f"{self.run_dir}/{sdc_filename}"
        with open(post_synth_sdc,'r') as f_old:
            lines=f_old.readlines()
            with open(new_post_synth_sdc,'w') as f_new:
                i = 0
                while i < len(lines):
                    line = lines[i]
                    words = line.strip().split()
                    if line.startswith("set_units") and len(words) >= 3:
                        unit_type = words[1]
                        value=words[2].split('.')[0]
                        units=words[2].replace('.','')
                        for c in value:
                            if not c.isnumeric():
                                value=value.replace(c,'')
                        for c in units:
                            if c.isnumeric():
                                units=units.replace(c,'')
                        if value == '1000' and len(units) >= 2:
                            value='1'
                            units=self.scale_units_1000x_down(units[0])+units[1:]
                        line=f"set_units {words[1]} {value}{units}\n"

                    if line.startswith("group_path"):
                        while (lines[i].strip().endswith('\\') and i < len(lines)-1):
                            i=i+1
                    else:
                        f_new.write(line)
                    i=i+1
        return new_post_synth_sdc

    def generate_sdc_files(self) -> List[str]:
        sdc_files = []  # type: List[str]

        # Generate constraints
        clock_constraints_fragment = os.path.join(self.run_dir, "clock_constraints_fragment.sdc")
        with open(clock_constraints_fragment, "w") as f:
            f.write(self.sdc_clock_constraints)
        sdc_files.append(clock_constraints_fragment)

        # Generate port constraints.
        pin_constraints_fragment = os.path.join(self.run_dir, "pin_constraints_fragment.sdc")
        with open(pin_constraints_fragment, "w") as f:
            f.write(self.sdc_pin_constraints)
        sdc_files.append(pin_constraints_fragment)

        # Add the post-synthesis SDC, if present.
        post_synth_sdc = self.post_synth_sdc
        if post_synth_sdc is not None:
            self.post_synth_sdc = self.process_sdc_file(self.post_synth_sdc)
            sdc_files.append(self.post_synth_sdc)

        return sdc_files

def openroad_global_settings(ht: HammerTool) -> bool:
    """Settings that need to be reapplied at every tool invocation"""
    assert isinstance(ht, HammerPlaceAndRouteTool)
    assert isinstance(ht, OpenROADTool)
    assert isinstance(ht, TCLTool)
    ht.create_enter_script()

    # Generic settings
    ht.append("# OpenROAD TCL Script")

    return True

tool = OpenROADPlaceAndRoute
