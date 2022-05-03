#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenROAD-flow par plugin for Hammer
#
# See LICENSE for licence details.

# NOTE: any hard-coded values are from OpenROAD example flow

import glob
import os
import platform
import subprocess
from datetime import datetime
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from hammer_logging import HammerVLSILogging
from hammer_utils import deepdict, optional_map
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, HammerToolStep, HammerToolHookAction, MMMCCornerType, PlacementConstraintType, TCLTool
from hammer_vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer_vlsi.vendor import OpenROADTool, OpenROADPlaceAndRouteTool

import hammer_tech
from hammer_tech import RoutingDirection
import specialcells
from specialcells import CellType, SpecialCell

# TODO: replace all $::env(HAMMER_HOME) with keys from hammer


class OpenROADPlaceAndRoute(OpenROADPlaceAndRouteTool, TCLTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            self.floorplan_design,
            self.place_tap_cells,
            self.power_straps,
            self.global_placement,
            self.place_pins,
            self.place_opt_design,
            self.clock_tree,
            self.add_fillers,
            self.route_design,
            # self.opt_design,
            # self.write_regs, # nop
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
        assert super().do_pre_steps(first_step)
        # self.cmds = []
        # Restore from the last checkpoint if we're not starting over.
        if first_step != self.first_step:
            self.append("read_db pre_{step}".format(step=first_step.name))
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.append("write_db pre_{step}".format(step=next.name))
        # Symlink the database to latest for open_chip script later.
        self.append("ln -sfn pre_{step} latest".format(step=next.name))
        self._step_transitions = self._step_transitions + [(prev.name, next.name)]
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
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
    def output_spef_paths(self) -> List[str]:
        return os.path.join(self.run_dir, "{top}.par.spef".format(top=self.top_module))

    @property
    def route_guide_path(self) -> List[str]:
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

    def block_append(self,commands) -> bool:
        for line in commands.split('\n'):
            self.append(line.strip())
            # if line.strip().startswith('#') or (line==""):
            #     self.append(line.strip())
            # else:
            #     self.verbose_append(line.strip())
        return True

    def fill_outputs(self) -> bool:
        # TODO: no support for ILM
        self.output_ilms = []

        self.output_gds = self.output_gds_filename
        self.output_netlist = self.output_netlist_filename
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
        """
        Package a tarball of the design for submission to OpenROAD developers.
        Based on the make <design>_issue target in OpenROAD-flow-scripts/flow/util/utils.mk

        TODOs:
        - Check error code to determine if this needs to actually be done
        - Split par.tcl into constituent steps, conditional filter out everything after floorplan
        - Conditional copy/sourcing of LEFs & LIBs
        - Conditional copy of .pdn file
        """
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        tag = f"{self.top_module}_{platform.platform()}_{now}"
        issue_dir = os.path.join(self.run_dir, tag)
        os.mkdir(issue_dir)

        # Dump the log
        with open(os.path.join(issue_dir, f"{self.top_module}.log")) as f:
            f.write(output)

        # runme script
        runme = os.path.join(issue_dir, "runme.sh")
        with open(runme) as f:
            f.write("#!/bin/bash")
            f.write("openroad -no_init -exit par.tcl")
        os.chmod(runme, 0o755) # +x

        # Gather files in self.run_dir
        file_exts = [".tcl", ".sdc", ".pdn", ".lef"]
        for match in list(filter(lambda x: any(ext in file_exts for ext in x, os.listdir(self.run_dir)))):
            shutil.copy2(os.path.join(self.run_dir, match), os.path.join(issue_dir, match))

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

        # Tar up the directory
        subprocess.call(["tar", "-zcf", f"{tag}.tar.gz", issue_dir])

        return True


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
            f.write("read_db latest")

        with open(self.open_chip_script, "w") as f:
            f.write("""#!/bin/bash
        cd {run_dir}
        source enter
        $OPENROAD_BIN -no_init -gui {open_chip_tcl}
                """.format(run_dir=self.run_dir, open_chip_tcl=self.open_chip_tcl))
        os.chmod(self.open_chip_script, 0o755)

        # Build args.
        args = [
            self.get_setting("par.openroad.openroad_bin"),
            "-no_init",             # do not read .openroad init file
            "-exit",                # exit after reading par_tcl_filename
            # this log prevents any output from showing in terminal, even with verbose_append
            # "-log openroad.log",    # write a log in <file_name>
            par_tcl_filename
        ]

        if bool(self.get_setting("par.openroad.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + " ".join(args))
        else:
            # Temporarily disable colours/tag to make run output more readable.
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable(args, cwd=self.run_dir)  # TODO: check for errors and deal with them
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

        # TODO: check that par run was successful

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
            self.append(f"read_lef {new_lef_file}")
        self.append("")
        return True

    def read_liberty(self) -> bool:
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

            self.append(f"define_corners {' '.join(corner_names)}")
            for corner,corner_name in zip(corners,corner_names):
                lib_files=self.get_timing_libs(corner)
                for lib_file in lib_files.split():
                    self.verbose_append(f"read_liberty -corner {corner_name} {lib_file}")
        self.append("")

    def convert_units(self,prefix) -> str:
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
        # TODO: make this more elegant

        sdc_files = self.generate_sdc_files()
        for sdc_file in sdc_files:
            self.append(f"read_sdc -echo {sdc_file}")

        return True

    #========================================================================
    # par main steps
    #========================================================================
    def init_design(self) -> bool:
        self.read_lef()
        self.read_liberty()

        # read_verilog
        # We are switching working directories and we still need to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        for verilog_file in abspath_input_files:
            self.append(f"read_verilog {verilog_file}")
        self.append(f"link_design {self.top_module}\n")
        self.read_sdc()
        return True

    def floorplan_design(self) -> bool:
        # TODO: place macros
        floorplan_tcl_path = os.path.join(self.run_dir, "floorplan.tcl")
        with open(floorplan_tcl_path, "w") as f:
            # print(self.create_floorplan_tcl())
            f.write("\n".join(self.create_floorplan_tcl()))

        self.block_append(f"""
        ################################################################
        # Floorplan Design
        source -echo -verbose {floorplan_tcl_path}
        # source $::env(HAMMER_HOME)/src/hammer-vlsi/technology/sky130/extra/sky130hd.tracks

        # remove buffers inserted by synthesis
        remove_buffers

        # IO Placement (random)
        {self.place_pins_tcl(random=True)}
        """)

        # TODO: macro placement
        # Macro Placement
        # if { [have_macros] } {
        #   global_placement -density $global_place_density
        #   macro_placement -halo $macro_place_halo -channel $macro_place_channel
        # }
        return True

    def place_tap_cells(self) -> bool:
        tap_cells = self.technology.get_special_cell_by_type(CellType.TapCell)
        endcap_cells = self.technology.get_special_cell_by_type(CellType.EndCap)
        if len(tap_cells) == 0:
            self.logger.warning("Tap cells are improperly defined in the tech plugin and will not be added. This step should be overridden with a user hook.")
            return True
        tap_cell = tap_cells[0].name[0]
        endcap_cell=endcap_cells[0].name[0]
        try:
            interval = self.get_setting("vlsi.technology.tap_cell_interval")
            offset = self.get_setting("vlsi.technology.tap_cell_offset")
            self.block_append(f"""
            ################################################################
            # Tapcell insertion
            tapcell -tapcell_master {tap_cell} -endcap_master {endcap_cell} -distance {interval} -halo_width_x {offset} -halo_width_y {offset}
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
        std_cell_rail_layer = str(self.get_setting("technology.core.std_cell_rail_layer"))
        strap_layers.insert(0,std_cell_rail_layer)

        metal_pairs=""
        for i in range(0,len(strap_layers)-1):
            metal_pairs+=f"{{{strap_layers[i]} {strap_layers[i+1]}}} "

        global_connections_pwr=[]
        for pwr_net in pwr_nets:
            if pwr_net.tie is not None:
                global_connections_pwr.append(f"\n{{inst_name .* pin_name {pwr_net.name}}}")

        global_connections_gnd=[]
        for gnd_net in gnd_nets:
            if gnd_net.tie is not None:
                global_connections_gnd.append(f"\n{{inst_name .* pin_name {gnd_net.name}}}")

        pdn_cfg=f"""
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
            {primary_pwr_net} {{
                {' '.join(global_connections_pwr)}
        }}
            {primary_gnd_net} {{
                {' '.join(global_connections_gnd)}
            }}
        }}
        ##===> Power grid strategy
        # Ensure pitches and offsets will make the stripes fall on track

        pdngen::specify_grid stdcell {{
            name grid
            rails {{
                met1 {{width 0.48 offset 0}}
            }}
            straps {{
                {' '.join(self.create_power_straps_tcl())}
            }}
            connect {{{metal_pairs}}}
        }}

        pdngen::specify_grid macro {{
            orient {{R0 R180 MX MY}}
            power_pins  "{' '.join(self.get_setting("technology.core.std_cell_supplies.power"))}"
            ground_pins "{' '.join(self.get_setting("technology.core.std_cell_supplies.ground"))}"
            blockages "{" ".join(all_metal_layer_names[:-1])}"
            # TODO: where does this met4_PIN_ver come from????
            connect {{{{met4_PIN_ver met5}}}}
            # or: connect {{{{met4_PIN_hor met5}}}}
        }}
        """

        with open(pdn_config_path, "w") as f:
            f.write(pdn_cfg)

    def power_straps(self) -> bool:
        """Place the power straps for the design."""
        pdn_config_path = os.path.join(self.run_dir, "power_straps.pdn")
        self.generate_pdn_config(pdn_config_path)
        self.block_append(f"""
        ################################################################
        # Power distribution network insertion
        pdngen -verbose {pdn_config_path}
        """)
        return True

    def global_placement(self) -> bool:
        # TODO: generate sky130hd.rc ourselves
        # TODO: try leaving out clock
        # TODO: try without set_wire_rc

        self.block_append("""
        ################################################################
        # Global placement
        """)
        metals=self.get_stackup().metals[1:]
        for metal in metals:
            self.append(f"set_global_routing_layer_adjustment {metal.name} 0.5")
        self.block_append(f"""
        set_routing_layers -signal {metals[0].name}-{metals[-1].name} -clock met3-met5
        set_macro_extension 2

        global_placement -routability_driven -density 0.3 -pad_left 4 -pad_right 4
        """)

        return True

    def place_pins_tcl(self,random=False) -> str:
        # TODO: investigate order of place_pins (i.e. ordered by port declaration??)
        # TODO: add -group_pins flag (what happens when called for multiple groups)
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
        if not (hor_layers and ver_layers):
            self.logger.warning("Both horizontal and vertical pin layers should be specified. Hammer will auto-specify one or both.")
            # choose first pin layer to be middle of stackup
            #   or use pin layer in either hor_layers or ver_layers
            pin_layer_names=["",""]
            pin_layer_names[0]=all_metal_layer_names[int(len(all_metal_layer_names)/2)]
            # pin_layer_name1=self.get_stackup().get_metal_by_index(int(len(self.get_stackup().metals)/2))
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
        return f"place_pins {random_arg} -hor_layers {{{' '.join(hor_layers)}}} -ver_layers {{{' '.join(ver_layers)}}}"

    def place_pins(self) -> bool:
        self.block_append(f"""
        ################################################################
        # IO Placement
        {self.place_pins_tcl()}

        write_def "{self.run_dir}/{self.top_module}_global_place.def"
        """)
        return True

    def place_opt_design(self) -> bool:
        self.block_append(f"""
        ################################################################
        # Repair max slew/cap/fanout violations and normalize slews
        source "$::env(HAMMER_HOME)/src/hammer-vlsi/technology/sky130/extra/sky130hd.rc"
        set_wire_rc -signal -layer "met2"
        set_wire_rc -clock  -layer "met5"
        """)

        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)
        tie_hilo_cells = self.technology.get_special_cell_by_type(CellType.TieHiLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1:
            self.logger.warning("Hi and Lo tiecells are unspecified or improperly specified and will not be added during synthesis.")
        else:
            tie_hi_cell = tie_hi_cells[0].name[0]
            tie_hi_port = tie_hi_cells[0].input_ports[0]
            tie_lo_cell = tie_lo_cells[0].name[0]
            tie_lo_port = tie_lo_cells[0].input_ports[0]

        self.block_append(f"""
        ################################################################
        # Repair max slew/cap/fanout violations and normalize slews
        set_dont_use {{{' '.join(self.get_dont_use_list())}}}
        estimate_parasitics -placement
        repair_design -slew_margin 0 -cap_margin 0

        repair_tie_fanout -separation 5 "{tie_hi_cell}/{tie_hi_port}"
        repair_tie_fanout -separation 5 "{tie_lo_cell}/{tie_lo_port}"

        # default detail_place_pad value in OpenROAD = 2
        set_placement_padding -global -left 2 -right 2
        detailed_placement

        # post resize timing report (ideal clocks)
        report_worst_slack -min -digits 3
        report_worst_slack -max -digits 3
        report_tns -digits 3

        # Check slew repair
        report_check_types -max_slew -max_capacitance -max_fanout -violators
        """)
        return True

    def clock_tree(self) -> bool:
        self.block_append(f"""
        ################################################################
        # Clock Tree Synthesis
        repair_clock_inverters
        clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_1 -buf_list sky130_fd_sc_hd__clkbuf_1 -sink_clustering_enable

        # CTS leaves a long wire from the pad to the clock tree root.
        repair_clock_nets

        # place clock buffers
        detailed_placement

        # checkpoint
        write_def {self.run_dir}/{self.top_module}_cts.def

        ################################################################
        # Setup/hold timing repair

        set_propagated_clock [all_clocks]

        # -placement|-global_routing
        estimate_parasitics -placement

        repair_timing

        # Post timing repair.
        report_worst_slack -min -digits 3
        report_worst_slack -max -digits 3
        report_tns -digits 3
        """)
        return True

    def add_fillers(self) -> bool:
        """add decap and filler cells"""
        # TODO: EDIT THIS ALL DOWN!!!
        decaps = self.technology.get_special_cell_by_type(CellType.Decap)
        stdfillers = self.technology.get_special_cell_by_type(CellType.StdFiller)
        if len(decaps) == 0:
            self.logger.info("The technology plugin 'special cells: decap' field does not exist. It should specify a list of decap cells. Filling with stdfiller instead.")
        else:
            decap_cells = decaps[0].name
            decap_caps = []  # type: List[float]
            if decaps[0].size is not None:
                decap_caps = list(map(lambda x: CapacitanceValue(x).value_in_units("fF"), decaps[0].size))
            if len(decap_cells) != len(decap_caps):
                self.logger.error("Each decap cell in the name list must have a corresponding decapacitance value in the size list.")
            decap_consts = list(filter(lambda x: x.target=="capacitance", self.get_decap_constraints()))
            if len(decap_consts) > 0:
                if decap_caps is None:
                    self.logger.warning("No decap capacitances specified but decap constraints with target: 'capacitance' exist. Add decap capacitances to the tech plugin!")
                else:
                    for (cell, cap) in zip(decap_cells, decap_caps):
                        self.append("add_decap_cell_candidates {CELL} {CAP}".format(CELL=cell, CAP=cap))
                    for const in decap_consts:
                        assert isinstance(const.capacitance, CapacitanceValue)
                        area_str = ""
                        if all(c is not None for c in (const.x, const.y, const.width, const.height)):
                            assert isinstance(const.x, Decimal)
                            assert isinstance(const.y, Decimal)
                            assert isinstance(const.width, Decimal)
                            assert isinstance(const.height, Decimal)
                            area_str = " ".join(("-area", str(const.x), str(const.y), str(const.x+const.width), str(const.y+const.height)))
                        self.append("add_decaps -effort high -total_cap {CAP} {AREA}".format(
                            CAP=const.capacitance.value_in_units("fF"), AREA=area_str))
        if len(stdfillers) == 0:
            self.logger.warning(
                "The technology plugin 'special cells: stdfiller' field does not exist. It should specify a list of (non IO) filler cells. No filler will be added. You can override this with an add_fillers hook if you do not specify filler cells in the technology plugin.")
        else:
            # Decap cells as fillers
            if len(decaps) > 0:
                fill_cells = list(map(lambda c: str(c), decaps[0].name))
                # self.append("set_db add_fillers_cells \"{FILLER}\"".format(FILLER=" ".join(fill_cells)))
                # Targeted decap constraints
                decap_consts = list(filter(lambda x: x.target=="density", self.get_decap_constraints()))
                for const in decap_consts:
                    area_str = ""
                    if all(c is not None for c in (const.x, const.y, const.width, const.height)):
                        assert isinstance(const.x, Decimal)
                        assert isinstance(const.y, Decimal)
                        assert isinstance(const.width, Decimal)
                        assert isinstance(const.height, Decimal)
                        area_str = " ".join(("-area", str(const.x), str(const.y), str(const.x+const.width), str(const.y+const.height)))
                    self.append("add_fillers -density {DENSITY} {AREA}".format(
                        DENSITY=str(const.density), AREA=area_str))
                # Or, fill everywhere if no decap constraints given
                # if len(self.get_decap_constraints()) == 0:
                    # TODO: INV setting: self.append("add_fillers")

            # TODO: INV setting: self.append("set_db add_fillers_cells \"{FILLER}\"".format(FILLER=" ".join(fill_cells)))
            # TODO: INV setting:self.append("add_fillers")

            # Then the rest is stdfillers
            self.fill_cells = '{'+' '.join(list(map(lambda c: str(c), stdfillers[0].name)))+'}'
            self.block_append(f"""
            ################################################################
            # Detailed +  Filler Placement (final)

            detailed_placement
            # Capture utilization before fillers make it 100%
            utl::metric "utilization" [format %.1f [expr [rsz::utilization] * 100]]
            utl::metric "design_area" [sta::format_area [rsz::design_area] 0]
            filler_placement {self.fill_cells}
            check_placement -verbose
            """)
        return True

    def route_design(self) -> bool:
        self.block_append(f"""
        ################################################################
        # Global routing
        pin_access

        global_route -guide_file {self.route_guide_path} -congestion_iterations 100

        set antenna_report {self.run_dir}/{self.top_module}_ant.rpt
        set antenna_errors [check_antennas -report_violating_nets -report_file $antenna_report]
        utl::metric "ANT::errors" $antenna_errors
        if {{ $antenna_errors > 0 }} {{
          fail "found $antenna_errors antenna violations"
        }}
        """)

        self.block_append(f"""
        ################################################################
        # Detailed routing

        set_thread_count [exec getconf _NPROCESSORS_ONLN]
        detailed_route -guide {self.route_guide_path} \\
               -output_guide {self.run_dir}/{self.top_module}_output_guide.mod \\
               -output_drc {self.run_dir}/{self.top_module}_route_drc.rpt \\
               -output_maze {self.run_dir}/{self.top_module}_maze.log \\
               -verbose 0

        utl::metric "DRT::drv" [detailed_route_num_drvs]
        write_def {self.run_dir}/{self.top_module}_route.def
        """)
        return True

    def extraction(self) -> bool:
        sed_expr=r"{s/\\//g}"  # use sed find+replace to remove '\' character
        # TODO: generate this rcx_rules file
        self.block_append(f"""
        ################################################################
        # Extraction
        define_process_corner -ext_model_index 0 X

        extract_parasitics -ext_model_file {self.get_setting("par.inputs.openrcx_techfile")}

        write_spef {self.output_spef_paths}
        # remove backslashes in instances so that read_spef recognizes the instances
        exec sed -i {sed_expr} {self.output_spef_paths}

        read_spef {self.output_spef_paths}
        """)
        # alternative: use global routing based parasitics inlieu of rc extraction
        #   >> estimate_parasitics -global_routing
        return True

    def write_netlist(self) -> bool:
        # TODO: figure out how to remove physical-only cells
        # TODO: figure out how to emit flat verilog for LVS netlist (or is it default flat)
        self.append(f"write_verilog -include_pwr_gnd -remove_cells {self.fill_cells} {self.output_netlist_filename}")
        return True

    def write_gds(self) -> bool:
        # for some reason this gets executed last in example in OpenROAD-flow-scripts
        # klayout.lyt file is generated with sed command, sky130hd.lyt file is provided in OpenROAD-flow-scripts
        # write_gds
        gds_files = self.technology.read_libs([
            hammer_tech.filters.gds_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_gds = list(map(lambda ilm: ilm.gds, self.get_input_ilms()))
            gds_files.extend(ilm_gds)

        klayout_techfiles = self.technology.read_libs([
            hammer_tech.filters.klayout_techfile_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        klayout_techfile = klayout_techfiles[0]

        self.block_append(f"""
        # write gds
        exec klayout -zz \\
                -rd design_name={self.top_module} \\
                -rd in_def={self.output_def_filename} \\
                -rd in_files={" ".join(gds_files)} \\
                -rd seal_file= \\
                -rd config_file=$::env(HAMMER_HOME)/src/hammer-vlsi/technology/sky130/extra/fill.json \\
                -rd out_file={self.output_gds_filename} \\
                -rd tech_file={klayout_techfile} \\
                -rm $::env(HAMMER_HOME)/src/hammer-vlsi/technology/sky130/extra/def2stream.py
        """)
        # extra options:
        #   -rd in_files="$::env(GDSOAS_FILES) $::env(WRAPPED_GDSOAS)" \: all the extra gds files (set to GDS_FILES += $(BLOCK_GDS), BLOCK_GDS += ./results/$(PLATFORM)/$(DESIGN_NICKNAME)_$(block)/$(FLOW_VARIANT)/6_final.gds)
        #   -rd config_file=$fill_config \: ~OpenROAD-flow-scripts/flow/platforms/sky130hd/fill.json
        #   -rd seal_file=$seal_gds \: I think we can skip??
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
        # TODO: write all these to files!!!! (or process log to generate report)
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
        """)
        self.append(f"write_def {self.output_def_filename}")

        # TODO: look at IR drop analysis from ~OpenROAD-flow-scripts/flow/scripts/final_report.tcl
        # Static IR drop analysis

        # Write netlist
        self.write_netlist()

        # GDS streamout.
        self.write_gds()

        # Write SDF
        self.write_sdf()

        # Make sure that generated-scripts exists.
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        self.write_reports()

        self.ran_write_design=True

        return True



    @staticmethod
    def generate_chip_size_constraint(width: Decimal, height: Decimal, left: Decimal, bottom: Decimal, right: Decimal,
                                      top: Decimal, site: str) -> str:
        """
        Given chip width/height and margins, generate an Innovus TCL command to create the floorplan.
        Also requires a technology specific name for the core site
        """

        return f"initialize_floorplan -site {site} -die_area {{ 0 0 {width} {height}}} -core_area {{{left} {bottom} {width-right} {height-top}}}"

    def generate_make_tracks(self) -> List[str]:
        output = []
        # initialize_floorplan removes existing tracks
        #   --> use the make_tracks command to add routing tracks
        #       to a floorplan (with no arguments it uses default from tech LEF)
        layers = self.get_setting("par.generate_power_straps_options.by_tracks.strap_layers")
        for metal in self.get_stackup().metals:
            output.append(f"make_tracks {metal.name}")
        return output

    def create_floorplan_tcl(self) -> List[str]:
        """
        Create a floorplan TCL depending on the floorplan mode.
        """
        output = []  # type: List[str]

        floorplan_mode = str(self.get_setting("par.openroad.floorplan_mode"))
        if floorplan_mode == "manual":
            floorplan_script_contents = str(self.get_setting("par.openroad.floorplan_script_contents"))
            # TODO(edwardw): proper source locators/SourceInfo
            output.append("# Floorplan manually specified from HAMMER")
            output.extend(floorplan_script_contents.split("\n"))
        elif floorplan_mode == "generate":
            output.extend(self.generate_floorplan_tcl())
        elif floorplan_mode == "auto":
            output.append("# Using auto-generated floorplan")
            output.append("plan_design")
            spacing = self.get_setting("par.blockage_spacing")
            bot_layer = self.get_stackup().get_metal_by_index(1).name
            top_layer = self.get_setting("par.blockage_spacing_top_layer")
            if top_layer is not None:
                output.append("create_place_halo -all_blocks -halo_deltas {{{s} {s} {s} {s}}} -snap_to_site".format(
                    s=spacing))
                output.append("create_route_halo -all_blocks -bottom_layer {b} -space {s} -top_layer {t}".format(
                    b=bot_layer, t=top_layer, s=spacing))
        else:
            if floorplan_mode != "blank":
                self.logger.error("Invalid floorplan_mode {mode}. Using blank floorplan.".format(mode=floorplan_mode))
            # Write blank floorplan
            output.append("# Blank floorplan specified from HAMMER")
        return output

    def generate_floorplan_tcl(self) -> List[str]:

        """
        Generate a TCL floorplan for OpenROAD based on the input config/IR.
        Not to be confused with create_floorplan_tcl, which calls this function.
        """
        output = []  # type: List[str]

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
                if constraint.create_physical:
                    output.append("create_inst -cell {cell} -inst {inst} -location {{{x} {y}}} -orient {orientation} -physical -status fixed".format(
                        cell=constraint.master,
                        inst=new_path,
                        x=constraint.x,
                        y=constraint.y,
                        orientation=orientation
                    ))
                if constraint.type == PlacementConstraintType.Dummy:
                    pass
                elif constraint.type == PlacementConstraintType.Placement:
                    output.append("create_guide -name {name} -area {x1} {y1} {x2} {y2}".format(
                        name=new_path,
                        x1=constraint.x,
                        x2=constraint.x + constraint.width,
                        y1=constraint.y,
                        y2=constraint.y + constraint.height
                    ))
                elif constraint.type in [PlacementConstraintType.HardMacro, PlacementConstraintType.Hierarchical]:
                    output.append("place_inst {inst} {x} {y} {orientation}{fixed}".format(
                        inst=new_path,
                        x=constraint.x,
                        y=constraint.y,
                        orientation=orientation,
                        fixed=" -fixed" if constraint.create_physical else ""
                    ))
                    spacing = self.get_setting("par.blockage_spacing")
                    if constraint.top_layer is not None:
                        current_top_layer = constraint.top_layer #  type: Optional[str]
                    elif global_top_layer is not None:
                        current_top_layer = global_top_layer
                    else:
                        current_top_layer = None
                    if current_top_layer is not None:
                        bot_layer = self.get_stackup().get_metal_by_index(1).name
                        output.append("create_place_halo -insts {inst} -halo_deltas {{{s} {s} {s} {s}}} -snap_to_site".format(
                            inst=new_path, s=spacing))
                        output.append("create_route_halo -bottom_layer {b} -space {s} -top_layer {t} -inst {inst}".format(
                            inst=new_path, b=bot_layer, t=current_top_layer, s=spacing))
                elif constraint.type == PlacementConstraintType.Obstruction:
                    obs_types = get_or_else(constraint.obs_types, [])  # type: List[ObstructionType]
                    if ObstructionType.Place in obs_types:
                        output.append("create_place_blockage -area {{{x} {y} {urx} {ury}}}".format(
                            x=constraint.x,
                            y=constraint.y,
                            urx=constraint.x+constraint.width,
                            ury=constraint.y+constraint.height
                        ))
                    if ObstructionType.Route in obs_types:
                        output.append("create_route_blockage -layers {{{layers}}} -spacing 0 -{area_flag} {{{x} {y} {urx} {ury}}}".format(
                            x=constraint.x,
                            y=constraint.y,
                            urx=constraint.x+constraint.width,
                            ury=constraint.y+constraint.height,
                            area_flag="rects" if self.version() >= self.version_number("181") else "area",
                            layers="all" if constraint.layers is None else " ".join(get_or_else(constraint.layers, []))
                        ))
                    if ObstructionType.Power in obs_types:
                        output.append("create_route_blockage -pg_nets -layers {{{layers}}} -{area_flag} {{{x} {y} {urx} {ury}}}".format(
                            x=constraint.x,
                            y=constraint.y,
                            urx=constraint.x+constraint.width,
                            ury=constraint.y+constraint.height,
                            area_flag="rects" if self.version() >= self.version_number("181") else "area",
                            layers="all" if constraint.layers is None else " ".join(get_or_else(constraint.layers, []))
                        ))
                else:
                    assert False, "Should not reach here"
            output = []
        return [chip_size_constraint] + output + self.generate_make_tracks()

    def specify_std_cell_power_straps(self, blockage_spacing: Decimal, bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        """
        Generate a list of TCL commands that build the low-level standard cell power strap rails.
        This will use the -master option to create power straps based on technology.core.tap_cell_rail_reference.
        The layer is set by technology.core.std_cell_rail_layer, which should be the highest metal layer in the std cell rails.

        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power net names (e.g. ["VDD", "VSS"]). Currently only two are supported.
        :return: A list of TCL commands that will generate power straps on rails.
        """
        return []

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
        return [f"\n{layer_name} {{width {width} pitch {pitch} offset {offset}}}"]

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
                        value=words[2].split('.')[0]
                        units=words[2].replace('.','')
                        for c in value:
                            if not c.isnumeric():
                                value=value.replace(v,'')
                        for c in units:
                            if c.isnumeric():
                                units=units.replace(c,'')
                        if value == '1000' and len(units) >= 2:
                            value='1'
                            units=self.convert_units(units[0])+units[1:]
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
