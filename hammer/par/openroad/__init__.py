# OpenROAD-flow par plugin for Hammer
#
# See LICENSE for licence details.

# NOTE: any hard-coded values are from OpenROAD example flow

import os
import shutil
import errno
import platform
import subprocess
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Callable
from decimal import Decimal
from pathlib import Path
from textwrap import indent, dedent

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
            self.global_placement,
            self.io_placement,
            self.resize,
            self.detailed_placement,
            # CTS
            self.clock_tree,
            self.clock_tree_resize,
            self.add_fillers,
            # ROUTING
            self.global_route,
            self.global_route_resize,
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

    @property
    def _steps_to_run(self) -> List[str]:
        """
        Private helper property to keep track of which steps we ran so that we
        can create symlinks.
        This is a list of (pre, post) steps
        """
        return self.attr_getter("__steps_to_run", [])

    @_steps_to_run.setter
    def _steps_to_run(self, value: List[str]) -> None:
        self.attr_setter("__steps_to_run", value)


    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        self.created_archive = False
        self.ran_write_design = False
        if self.create_archive_mode  == "latest_run":
            # since OpenROAD won't be run, get OpenROAD "output" from previous run's log
            if not os.path.exists(self.openroad_latest_log):
                self.logger.error("""ERROR: OpenROAD place-and-route must be run before creating an archive. To fix this error:
        1. In your YAML configs, set par.openroad.create_archive_mode : none
        2. Re-run the previous command
        3. Set par.openroad.create_archive_mode : latest_run""")
                exit(1)
            self.logger.warning("Skipping place-and-route run and creating an archive of the latest OpenROAD place-and-route run (because par.openroad.create_archive_mode key was set to 'latest_run')")
            # NOTE: openroad log will be empty if OpenROAD was terminated (e.g. by Ctrl-C)
            with open(self.openroad_latest_log,'r') as f:
                output = f.read()
            self.create_archive(output,0)  # give it a zero exit code to indicate OpenROAD didn't error before this
            exit(0)
        assert super().do_pre_steps(first_step)
        # Restore from the last checkpoint if we're not starting over.
        if first_step != self.first_step:
            self.init_design(first_step=first_step)
        self._steps_to_run = self._steps_to_run + [first_step.name]

        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.block_append("write_db pre_{step}".format(step=next.name))
        # Symlink the database to latest for open_chip script later.
        self.block_append("exec ln -sfn pre_{step} latest".format(step=next.name))
        self._step_transitions = self._step_transitions + [(prev.name, next.name)]
        self._steps_to_run = self._steps_to_run + [next.name]
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
        if len(self._steps_to_run) > 0:
            last = "post_{step}".format(step=self._steps_to_run[-1])
            self.block_append("write_db {last}".format(last=last))
            # Symlink the database to latest for open_chip script later.
            self.block_append("exec ln -sfn {last} latest".format(last=last))

        return self.run_openroad()

    @property
    def all_regs_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_paths.json")

    @property
    def all_cells_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_cells.json")

    @property
    def output_sdf_path(self) -> str:
        return os.path.join(self.run_dir, "{top}.par.sdf.gz".format(top=self.top_module))

    @property
    def output_spef_paths(self) -> List[str]:
        return [os.path.join(self.run_dir, "{top}.par.spef".format(top=self.top_module))]

    @property
    def route_guide_path(self) -> str:
        return os.path.join(self.run_dir, "{top}.route_guide".format(top=self.top_module))

    @property
    def env_vars(self) -> Dict[str, str]:
        v = dict(super().env_vars)
        v["OPENROAD_BIN"] = self.get_setting('par.openroad.openroad_bin')
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
    def openroad_latest_log(self) -> str:
        return os.path.join(self.run_dir,"openroad.log")

    @property
    def create_archive_mode(self) -> str:
        return self.get_setting('par.openroad.create_archive_mode')

    @property
    def reports_dir(self) -> str:
        return os.path.join(self.run_dir, "reports")

    @property
    def metrics_dir(self) -> str:
        return os.path.join(self.run_dir, "metrics")

    @property
    def metrics_file(self) -> str:
        return os.path.join(self.metrics_dir, f"metrics-{self._steps_to_run[-1]}.json")

    @property
    def fill_cells(self) -> str:
        stdfillers = self.technology.get_special_cell_by_type(CellType.StdFiller)
        return ' '.join(list(map(lambda c: str(c), stdfillers[0].name)))
    
    @property
    def timing_driven(self) -> bool:
        return self.get_setting('par.openroad.timing_driven')

    def reports_path(self, rpt_name) -> str:
        return os.path.join(self.reports_dir, rpt_name)

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


    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["par.outputs.seq_cells"] = self.output_seq_cells
        outputs["par.outputs.all_regs"] = self.output_all_regs
        outputs["par.outputs.sdf_file"] = self.output_sdf_path
        outputs["par.outputs.spefs"] = self.output_spef_paths
        return outputs


    def fill_outputs(self) -> bool:
        # TODO: no support for ILM
        self.output_ilms = []

        self.output_gds = self.output_gds_filename
        self.output_netlist = self.output_netlist_filename
        self.output_sim_netlist = self.output_sim_netlist_filename

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


        if self.ran_write_design:
            if not os.path.isfile(self.output_gds_filename):
                raise ValueError("Output GDS %s not found" % (self.output_gds_filename))

            if not os.path.isfile(self.output_netlist_filename):
                raise ValueError("Output netlist %s not found" % (self.output_netlist_filename))

            if not os.path.isfile(self.output_sim_netlist_filename):
                raise ValueError("Output sim netlist %s not found" % (self.output_sim_netlist_filename))

            if not os.path.isfile(self.output_sdf_path):
                raise ValueError("Output SDF %s not found" % (self.output_sdf_path))

            for spef_path in self.output_spef_paths:
                if not os.path.isfile(spef_path):
                    raise ValueError("Output SPEF %s not found" % (spef_path))

        else:
            self.logger.info("Did not run write_design")


        return True

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
        file_exts = [".tcl", ".sdc", ".lef"]
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

        # RC file
        setrc_file = self.get_setting('par.openroad.setrc_file')
        if setrc_file and os.path.exists(setrc_file):
            shutil.copy2(setrc_file, os.path.join(issue_dir, os.path.basename(setrc_file)))

        # RCX File
        openrcx_files = self.get_setting('par.openroad.openrcx_techfiles')
        for openrcx_file in openrcx_files:
            if os.path.exists(openrcx_file):
                shutil.copy2(openrcx_file, os.path.join(issue_dir, os.path.basename(openrcx_file)))
        
        # KLayout tech file
        klayout_techfile_path = self.setup_klayout_techfile()
        if klayout_techfile_path and os.path.exists(klayout_techfile_path):
            shutil.copy2(klayout_techfile_path, os.path.join(issue_dir, os.path.basename(klayout_techfile_path)))
        
        # DEF2Stream file
        def2stream_file = self.get_setting('par.openroad.def2stream_file')
        if os.path.exists(def2stream_file):
            shutil.copy2(def2stream_file, os.path.join(issue_dir, os.path.basename(def2stream_file)))

        # Hack par.tcl script
        # Remove abspaths to files since they are now in issue_dir
        subprocess.call(["sed", "-i", "-E", r"/repair_tie_fanout/! s#(/[^/ ]+)+/([^/ ]+/)*([^/ ]+)#\3#g", os.path.join(issue_dir, "par.tcl")])
        # Comment out exec klayout block
        klayout_bin = self.get_setting('par.openroad.klayout_bin')
        subprocess.call(["sed", "-i", f"s/\(exec {klayout_bin}\)/# \\1/g", os.path.join(issue_dir, "par.tcl")])

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
        cmds: List[str] = []
        self.block_tcl_append(f"""
        set db_name $::env(db_name)
        set timing $::env(timing)

        if {{$timing}} {{
            {indent(self.read_liberty(), prefix=3*4*' ').strip()}
        }}

        """, cmds, clean=True, verbose=False)

        # cmds.append(self.read_liberty())
        self.block_tcl_append("""
        puts "Reading $db_name database..."
        read_db $db_name
        """, cmds, clean=True, verbose=False)

        step_names = [s.name for s in self.steps]
        self.block_tcl_append(f"""
        # Determine step & index
        set steps {{ {' '.join(step_names)} }}
        """, cmds, clean=True, verbose=False)
        self.block_tcl_append("""
        set step [string map {pre_ ""} $db_name]
        set step [string map {post_ ""} $step]
        set step_idx [lsearch $steps $step]
        if { [string range $db_name 0 3] == "pre_" } {
            set step_idx [expr $step_idx - 1]
        }
        set step [lindex $steps $step_idx]
        """, cmds, clean=True, verbose=False)

        spef_file  = self.output_spef_paths[0]
        self.block_tcl_append(f"""
        if {{$timing}} {{
            # TODO: need to read a later SDC with updated clock constraints?
            {indent(self.read_sdc(), prefix=3*4*' ').strip()}
            {self.set_rc()}
            if {{ $step_idx >= [lsearch $steps "clock_tree"] }} {{
                puts "Post-CTS, propagate clocks..."
                set_propagated_clock [all_clocks]
            }}

            if {{ ($step_idx >= [lsearch $steps "extraction"]) && ([file exists {spef_file}] == 1) }} {{
                puts "Post-extraction, reading SPEF..."
                {indent(self.read_spef(), prefix=4*4*' ').strip()}
            }} elseif {{ $step_idx >= [lsearch $steps "global_route"] }} {{
                puts "Post-global_route & pre-extraction, estimating parasitics from global route..."
                estimate_parasitics -global_routing
            }} elseif {{ $step_idx >= [lsearch $steps "global_placement"] }} {{
                puts "Post-global_placement & pre-global_route, estimating parasitics from placement..."
                estimate_parasitics -placement
            }}
        }}
        """, cmds, clean=True, verbose=False)
        self.block_tcl_append("""
        if {$timing} {
            puts "Timing information loaded."
        } else {
            puts "Timing information not loaded."
            puts "  To load database with timing information, run: "
            puts "  ./generated_scripts/open_chip \[db_name\] timing"
        }
        puts "Loaded Step $step_idx: $step ($db_name)."

        """, cmds, clean=True, verbose=False)

        return '\n'.join(cmds)

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_openroad(self) -> bool:
        # Quit OpenROAD.
        self.block_append("exit")

        # Create reports directory
        os.makedirs(self.reports_dir, exist_ok=True)

        # Create metrics directory
        os.makedirs(self.metrics_dir, exist_ok=True)

        # Create par script.
        par_tcl_filename = os.path.join(self.run_dir, "par.tcl")
        with open(par_tcl_filename, "w") as f:
            f.write("\n".join(self.output))

        # Make sure that generated-scripts exists.
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        # Create open_chip script pointing to latest (symlinked to post_<last ran step>).
        with open(self.open_chip_tcl, "w") as f:
            f.write(self.gui())

        with open(self.open_chip_script, "w") as f:
            f.write(dedent(f"""\
        #!/bin/bash

        usage() {{
            echo ""
            echo "Usage: ${{0}} [-t] [openroad_db_name]"
            echo ""
            echo "Options"
            echo "  openroad_db_name    : Name of database to load (default=latest)"
            echo "  -t, --timing        : Load timing info (default=disabled because of slow load time)"
            echo "  -h, --help          : Display this message"
            echo ""
            exit
        }}

        cd {self.run_dir}
        source enter

        export db_name=$(readlink latest)
        export timing=0

        while [ "$1" != "" ];
        do
            case $1 in
                -h | --help )
                    usage ;;
                -t | --timing)
                    export timing=1 ;;
                * )
                    if [ -f $1 ]; then
                        export db_name=$1
                    else
                        error "invalid option $1"
                        usage
                    fi ;;
            esac
            shift
        done

        $OPENROAD_BIN -no_init -gui {self.open_chip_tcl}
        """))
        os.chmod(self.open_chip_script, 0o755)

        num_threads = str(self.get_setting('vlsi.core.max_threads'))

        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.openroad_log = os.path.join(self.run_dir,f"openroad-{now}.log")

        # Build args.
        args = [
            self.get_setting('par.openroad.openroad_bin'),
            "-no_init",             # do not read .openroad init file
            "-log", self.openroad_log,
            "-threads", num_threads,
            "-metrics", self.metrics_file,
            "-exit",                # exit after reading par_tcl_filename
            par_tcl_filename
        ]
        if bool(self.get_setting('par.openroad.generate_only')):
            self.logger.info("Generate-only mode: command-line is " + " ".join(args))
        else:
            output = self.run_executable(args, cwd=self.run_dir)
            if not self.created_archive and self.create_archive_mode  == "always":
                self.create_archive(output,0)  # give it a zero exit code to indicate OpenROAD didn't error before this
        # create reports
        self.log_to_reports()
        # copy openroad-{timestamp}.log to openroad.log
        shutil.copyfile(self.openroad_log, self.openroad_latest_log)
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

    def read_lef(self) -> str:
        # OpenROAD names the LEF libraries by filename:
        #   foo.tlef and foo.lef evaluate to the same library "foo"
        #   solution: copy foo.lef to foo1.lef
        cmds = [""]
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
            cmds.append(f"read_lef {lef_file}")
        cmds.append("")
        return '\n'.join(cmds)

    @property
    def corner_names(self) -> List[str]:
        corner_names = []
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        if corners:
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
        return corner_names


    def read_liberty(self) -> str:
        cmds=[]
        if self.corner_names:
            cmds.append(f"define_corners {' '.join(self.corner_names)}")
            for corner,corner_name in zip(self.get_mmmc_corners(),self.corner_names):
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

    def read_sdc(self) -> str:
        # overwrite SDC file to exclude group_path command
        # change units in SDC file (1000.0fF and 1000.0ps cause errors)

        cmds = [""]
        sdc_files = self.generate_sdc_files()
        for sdc_file in sdc_files[:-1]:
            cmds.append(f"read_sdc -echo {sdc_file}")
        cmds.append("")
        return '\n'.join(cmds)

    def set_rc(self) -> str:
        # set layer/wire RC
        cmd = ""
        setrc_file = self.get_setting('par.openroad.setrc_file')
        if setrc_file and os.path.exists(setrc_file):
            cmd = f"source {setrc_file}"
        else:
            self.logger.warning("OpenROAD par.openroad.setrc_file is not specified or does not exist. Layer capacitance/resistance values may be inaccurate.")
        return cmd

    #========================================================================
    # par main steps
    #========================================================================
    def init_design(self, first_step=None) -> bool:

        # start routine
        self.block_append(self.read_lef())
        self.block_append(self.read_liberty())

        if first_step and first_step != self.first_step:
            self.block_append(f"read_db pre_{first_step.name}")
        else:
            # read_verilog
            # We are switching working directories and we still need to find paths.
            abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
            for verilog_file in abspath_input_files:
                self.block_append(f"read_verilog {verilog_file}")
            self.block_append(f"link_design {self.top_module}\n")

        self.block_append(self.read_sdc())

        self.block_append(self.set_rc())

        self.block_append(f"""
        set_dont_use {{{' '.join(self.get_dont_use_list())}}}
        """)

        # step-dependent commands
        step_names = [s.name for s in self.steps]
        if first_step:
            if step_names.index(first_step.name) > step_names.index('clock_tree'):
                self.block_append("set_propagated_clock [all_clocks]")

            if step_names.index(first_step.name) > step_names.index('extraction') \
                and os.path.exists(self.output_spef_paths[0]):
                self.block_append(self.read_spef())
            elif step_names.index(first_step.name) > step_names.index('global_route'):
                self.block_append("estimate_parasitics -global_routing")
            elif step_names.index(first_step.name) > step_names.index('global_placement'):
                self.block_append("estimate_parasitics -placement")

        with open(self.write_reports_tcl, 'w') as f:
            f.write('\n'.join(self.create_write_reports_tcl()))

        self.block_append(f"source {self.write_reports_tcl}")

        self.block_append(r"""
        proc find_macros {} {
            set macros ""
            set block [[[ord::get_db] getChip] getBlock]
            foreach inst [$block getInsts] {
                set inst_master [$inst getMaster]
                if { [string match [$inst_master getType] "BLOCK"] } {
                    append macros [$inst getName] " "
                }
            }
            return $macros
        }
        """, verbose=False)

        return True

    @property
    def macros_list_file(self) -> str:
        return os.path.join(self.run_dir, "macros.txt")

    def floorplan_design(self) -> bool:

        floorplan_tcl = os.path.join(self.run_dir, "floorplan.tcl")
        with open(floorplan_tcl, "w") as f:
            f.write("\n".join(self.create_floorplan_tcl()))

        self.block_append(f"""
        ################################################################
        # Floorplan Design
        """)
        self.block_append(f"""
        # Print paths to macros to file
        set macros_file {self.macros_list_file}
        set macros_file [open $macros_file "w"]
        """, verbose=False)
        self.block_append(r"""
        set macros ""
        foreach macro [find_macros] {
            set inst [[ord::get_db_block] findInst $macro]
            set inst_master [$inst getMaster]
            append macros $macro " \n"
            append macros "\t- master: " [$inst_master getName] " \n"
            append macros "\t- width:  " [$inst_master getWidth] " \n"
            append macros "\t- height: " [$inst_master getHeight] " \n"
            set origin [$inst_master getOrigin]
            append macros "\t- origin: " [lindex $origin 0] ", " [lindex $origin 1] " \n"
        }
        puts $macros
        puts $macros_file $macros
        close $macros_file
        """, verbose=False)

        self.block_append(f"""
        # Init floorplan + Place Macros
        source -verbose {floorplan_tcl}

        # Make tracks
        # create routing tracks""")
        self.block_append(self.generate_make_tracks_tcl())
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
        if self.floorplan_mode == 'auto_macro':
            macro_orient = self.get_setting('par.openroad.macro_placement.orient_all')
            macro_orient = self.convert_orientation_hammer2openroad(macro_orient)
            halo = self.get_setting('par.openroad.macro_placement.halo')
            if len(halo) not in [1,2]:
                self.logger.error("Macro placement halo key 'par.openroad.macro_placement.halo' must be set as [vertical, horizontal] width pair.")
                return False
            if len(halo) == 1:
                halo += halo  # append to itself
            channel = self.get_setting('par.openroad.macro_placement.channel')
            if not channel:
                channel = [2*h for h in halo]
            halo = ' '.join([str(h) for h in halo])
            channel = ' '.join([str(c) for c in channel])
            padding = self.get_setting('par.openroad.global_placement.placement_padding')
            snap_layer = self.get_setting('par.openroad.macro_placement.snap_layer')
            stackup = self.get_stackup()
            snap_layer = stackup.get_metal(snap_layer).index

            self.block_append(f"""
            ################################################################
            # Auto Macro Placement
            set macros [find_macros]
            if {{ $macros != "" }} {{
                foreach macro $macros {{
                    place_cell -inst_name $macro -orient R90 -origin {{ 0 0 }} -status PLACED
                }}
                # Timing Driven Mixed Sized Placement
                global_placement -density 0.6 -pad_left {padding} -pad_right {padding}
                # ParquetFP-based macro cell placer, “TritonMacroPlacer”
                macro_placement -halo {{ {halo} }} -channel {{ {channel} }} -snap_layer {snap_layer}
            }}
            """, verbose=True)
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
            interval = self.get_setting('vlsi.technology.tap_cell_interval')
            offset = self.get_setting('vlsi.technology.tap_cell_offset')
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


    @property
    def macro_top_layers(self) -> List[str]:
        layers = set()
        floorplan_constraints = self.get_placement_constraints()
        global_top_layer = self.get_setting('par.blockage_spacing_top_layer')
        ############## Actually generate the constraints ################
        for constraint in floorplan_constraints:
            if constraint.top_layer is not None:
                layers.add(constraint.top_layer)
            elif global_top_layer is not None:
                layers.add(global_top_layer)
        return list(layers)


    def write_power_straps_tcl(self, power_straps_tcl_path) -> bool:
        pwr_nets=self.get_all_power_nets()
        gnd_nets=self.get_all_ground_nets()
        primary_pwr_net=pwr_nets[0].name
        primary_gnd_net=gnd_nets[0].name
        stackup = self.get_stackup()
        all_metal_layer_names = [layer.name for layer in stackup.metals]

        strap_layers = self.get_setting('par.generate_power_straps_options.by_tracks.strap_layers').copy()
        std_cell_rail_layer = str(self.get_setting('technology.core.std_cell_rail_layer'))
        strap_layers.insert(0,std_cell_rail_layer)

        add_pdn_connect_tcl=""
        for i in range(0,len(strap_layers)-1):
            add_pdn_connect_tcl+=f"add_pdn_connect -grid grid -layers {{{strap_layers[i]} {strap_layers[i+1]}}}\n"

        self.global_connections_tcl = ""
        for pwr_net in pwr_nets:
            if pwr_net.tie is not None:
                net = pwr_net.tie
            else:
                net = primary_pwr_net
            self.global_connections_tcl += f"\n add_global_connection -net {{{net}}} -inst_pattern {{.*}} -pin_pattern {{^{pwr_net.name}$}} -power"
        for gnd_net in gnd_nets:
            if gnd_net.tie is not None:
                net = gnd_net.tie
            else:
                net = primary_gnd_net
            self.global_connections_tcl += f"\n add_global_connection -net {{{net}}} -inst_pattern {{.*}} -pin_pattern {{^{gnd_net.name}$}} -ground"

        blockage_spacing = self.get_setting('par.blockage_spacing')
        blockage_spacing_halo = ' '.join([str(blockage_spacing) for i in range(4)])

        pdn_grid_tcl = ""
        i = 1
        for layer in self.macro_top_layers:
            layer_idx = stackup.get_metal(layer).index
            try:
                # get next layer up if it's valid
                # TODO: should restrict layers to those specified by power straps
                next_layer = stackup.get_metal_by_index(layer_idx+1).name
            except:
                continue

            grid1_name = f"CORE_macro_grid_{i}"
            grid2_name = f"CORE_macro_grid_{i+1}"
            i += 2
            pdn_grid_tcl += f"""
            ####################################
            # grid for: {grid1_name}
            ####################################
            define_pdn_grid -name {{{grid1_name}}} -voltage_domains {{CORE}} -macro -orient {{R0 R180 MX MY}} -halo {{ {blockage_spacing_halo} }} -default -grid_over_boundary
            add_pdn_connect -grid {{{grid1_name}}} -layers {{{layer} {next_layer}}}

            ####################################
            # grid for: {grid2_name}
            ####################################
            define_pdn_grid -name {{{grid2_name}}} -voltage_domains {{CORE}} -macro -orient {{R90 R270 MXR90 MYR90}} -halo {{ {blockage_spacing_halo} }} -default -grid_over_boundary
            add_pdn_connect -grid {{{grid2_name}}} -layers {{{layer} {next_layer}}}
            """

        tcl = f"""
        ####################################
        # global connections
        ####################################
        {self.global_connections_tcl}
        global_connect
        ####################################
        # voltage domains
        ####################################
        # AO is hard-coded in cpf generation too
        #   but OpenROAD errors when using AO instead of CORE
        set_voltage_domain -name {{CORE}} -power {{{primary_pwr_net}}} -ground {{{primary_gnd_net}}}
        ####################################
        # standard cell grid
        ####################################
        define_pdn_grid -name {{grid}} -voltage_domains {{CORE}}
        {' '.join(self.create_power_straps_tcl())}
        {add_pdn_connect_tcl}
        {pdn_grid_tcl}
        """

        with open(power_straps_tcl_path,'w') as power_straps_tcl_file:
            for line in tcl.split('\n'):
                power_straps_tcl_file.write(line.strip()+'\n')

        return True


    def power_straps(self) -> bool:
        """Place the power straps for the design."""
        # power_straps_tcl_path = os.path.join(self.run_dir, "power_straps.pdn")
        power_straps_tcl_path = os.path.join(self.run_dir, "power_straps.tcl")
        # self.generate_pdn_config(power_straps_tcl_path)
        self.write_power_straps_tcl(power_straps_tcl_path)
        self.block_append(f"""
        ################################################################
        # Power distribution network insertion
        # pdngen -verbose {power_straps_tcl_path}
        source -echo -verbose {power_straps_tcl_path}
        pdngen
        """)
        return True


    def place_pins_tcl(self,random=False) -> str:
        stackup = self.get_stackup()
        all_metal_layer_names = [layer.name for layer in stackup.metals]
        pin_assignments = self.get_pin_assignments()
        hor_layers=set()
        ver_layers=set()
        # TODO: fix how this is done if individual pins are specified
        for pin in pin_assignments:
            if pin.layers is not None and len(pin.layers) > 0:
                for pin_layer_name in pin.layers:
                    layer = stackup.get_metal(pin_layer_name)
                    if layer.direction==RoutingDirection.Horizontal:
                        hor_layers.add(pin_layer_name)
                    if layer.direction==RoutingDirection.Vertical:
                        ver_layers.add(pin_layer_name)

        # both hor_layers and ver_layers arguments are required
        # if missing, auto-choose one or both
        # TODO: Hammer currently throws an error if both horizontal + vertical pin layers are specified
        if not (hor_layers and ver_layers):
            self.logger.warning("Both horizontal and vertical pin layers should be specified. Hammer will auto-specify one or both.")
            # choose first pin layer to be middle of stackup
            #   or use pin layer in either hor_layers or ver_layers
            pin_layer_names=["",""]
            pin_layer_names[0]=all_metal_layer_names[int(len(all_metal_layer_names)/2)]
            if (hor_layers): pin_layer_names[0]=list(hor_layers)[0]
            if (ver_layers): pin_layer_names[0]=list(ver_layers)[0]
            pin_layer_idx_1=all_metal_layer_names.index(pin_layer_names[0])
            if (pin_layer_idx_1 < len(all_metal_layer_names)-1):
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1+1]
            elif (pin_layer_idx_1 > 0):
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1-1]
            else: # edge-case
                pin_layer_names[1]=all_metal_layer_names[pin_layer_idx_1]
            for pin_layer_name in pin_layer_names:
                layer = stackup.get_metal(pin_layer_name)
                if (layer.direction==RoutingDirection.Horizontal) and (pin_layer_name not in hor_layers):
                    hor_layers.add(pin_layer_name)
                if (layer.direction==RoutingDirection.Vertical)   and (pin_layer_name not in ver_layers):
                    ver_layers.add(pin_layer_name)
        # determine commands for side specified in pin assignments
        #   can only be done in openroad by "excluding" the entire length of the other 3 sides from pin placement
        cmds = ""
        if random:
                cmds += f"place_pins -random -hor_layers {{{' '.join(hor_layers)}}} -ver_layers {{{' '.join(ver_layers)}}}\n"
        else:
            for pin in pin_assignments:
                if ('*' not in pin.pins) and (pin.location is not None):
                    pin_layer_name = pin.layers[0] if pin.layers else all_metal_layer_names[-1]
                    cmd = [
                        "place_pin", "-pin_name", pin.pins,
                        "-layer", pin_layer_name,
                        "-location", f"{{{pin.location[0]} {pin.location[1]}}}",
                        "-pin_size", f"{{{pin.width} {pin.depth}}}",
                    ]
                    cmds += " ".join(list(cmd)) + '\n'
                else:
                    side=""
                    if pin.side == "bottom":
                        side="-exclude top:* -exclude right:* -exclude left:*"
                    elif pin.side == "top":
                        side="-exclude bottom:* -exclude right:* -exclude left:*"
                    elif pin.side == "left":
                        side="-exclude top:* -exclude right:* -exclude bottom:*"
                    elif pin.side == "right":
                        side="-exclude top:* -exclude bottom:* -exclude left:*"
                    cmds += f"place_pins -hor_layers {{{' '.join(hor_layers)}}} -ver_layers {{{' '.join(ver_layers)}}} {side}\n"
        return cmds.strip()

    def io_placement(self) -> bool:
        self.block_append(f"""
        ################################################################
        # IO Placement
        """)
        self.block_append(self.place_pins_tcl())
        return True


    def global_placement(self) -> bool:
        metals=self.get_stackup().metals[1:]
        routing_adj = self.get_setting('par.openroad.global_placement.routing_adjustment')
        spacing = self.get_setting('par.blockage_spacing')
        idx_clock_bottom_metal=min(2,len(metals)-1)
        density = self.get_setting('par.openroad.global_placement.density')
        padding = self.get_setting('par.openroad.global_placement.placement_padding')
        routability_driven = "-routability_driven" if self.get_setting('par.openroad.global_placement.routability_driven') else ""
        timing_driven = "-timing_driven" if self.timing_driven and self.get_setting('par.openroad.global_placement.timing_driven') else ""
        self.block_append(f"""
        ################################################################
        # Global placement (with placed IOs, timing-driven, and routability-driven)
        # set_dont_use {{{' '.join(self.get_dont_use_list())}}}
        # reduce the routing resources of all routing layers by X%
        set_global_routing_layer_adjustment {metals[0].name}-{metals[-1].name} {routing_adj}
        set_routing_layers -signal {metals[0].name}-{metals[-1].name} -clock {metals[idx_clock_bottom_metal].name}-{metals[-1].name}
        # creates blockages around macros
        # set_macro_extension {spacing}

        # -density default is 0.7, overflow default is 0.1
        global_placement -density {density} -pad_left {padding} -pad_right {padding} {routability_driven} {timing_driven}

        estimate_parasitics -placement
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
        buffer_ports
        # Perform buffer insertion
        # set_debug_level RSZ repair_net 1
        # insert buffers on nets to repair max slew, max capacitance, max fanout violations, and on long wires to reduce RC delay in the wire
        repair_design
        # -slew_margin 0 -cap_margin 0

        # Repair tie lo/hi fanout
        set tielo_lib_name [get_name [get_property [lindex [get_lib_cell {tie_lo_cell}] 0] library]]
        set tiehi_lib_name [get_name [get_property [lindex [get_lib_cell {tie_hi_cell}] 0] library]]
        repair_tie_fanout -separation 0 $tielo_lib_name/{tie_lo_cell}/{tie_lo_port}
        repair_tie_fanout -separation 0 $tiehi_lib_name/{tie_hi_cell}/{tie_hi_port}
        """)
        return True


    def detailed_placement(self) -> bool:
        padding = self.get_setting('par.openroad.detailed_placement.placement_padding')
        self.block_append(f"""
        ################################################################
        # Detail placement

        set_placement_padding -global -left {padding} -right {padding}
        detailed_placement

        # improve_placement
        optimize_mirroring

        estimate_parasitics -placement

        {self.write_reports(prefix='dpl')}
        """)
        return True

    def check_detailed_placement(self) -> bool:
        """
        for any step that runs the detailed_placement command,
            run this function at the start of the NEXT step
            so that the post-step database is saved and in the case of a check_placement error,
            the database may be opened in the OpenROAD gui for debugging the error
        """
        self.block_append(f"""
        # Check Detailed Placement
        check_placement -verbose
        """)
        return True

    @property
    def report_num_instances(self) -> str:
        return dedent("""puts "Design has [llength [get_cells *]] instances." """)

    def clock_tree(self) -> bool:
        self.check_detailed_placement()

        cts_buffer_cells = self.technology.get_special_cell_by_type(CellType.CTSBuffer)

        cts_args=""
        if cts_buffer_cells is None:
            self.logger.warning("CTS buffer cells are unspecified.")
        else:
            buf_list = list(map(lambda x: str(x), cts_buffer_cells[0].name))
            root_buf = buf_list[0]
            cts_args=f"""-root_buf {root_buf} -buf_list {{ {' '.join(buf_list)} }}"""

        padding_clock_tree = self.get_setting('par.openroad.clock_tree.placement_padding')

        self.block_append(f"""
        ################################################################
        # Clock Tree Synthesis
        # Run TritonCTS
        repair_clock_inverters

        clock_tree_synthesis {cts_args} -sink_clustering_enable \\
                                        -sink_clustering_size 30 \\
                                        -sink_clustering_max_diameter 100

        set_propagated_clock [all_clocks]

        estimate_parasitics -placement

        # CTS leaves a long wire from the pad to the clock tree root.
        repair_clock_nets

        estimate_parasitics -placement

        set_placement_padding -global -left {padding_clock_tree} -right {padding_clock_tree}

        # place clock buffers
        detailed_placement

        estimate_parasitics -placement
        """)
        return True

    def clock_tree_resize(self) -> bool:
        if self.timing_driven:
            setup_margin = self.get_setting('par.openroad.clock_tree_resize.setup_margin')
            hold_margin = self.get_setting('par.openroad.clock_tree_resize.hold_margin')
            hold_max_buffer_percent = self.get_setting('par.openroad.clock_tree_resize.hold_max_buffer_percent')
            padding_final = self.get_setting('par.openroad.clock_tree_resize.placement_padding')

            self.block_append(f"""
            ###########################
            # Post-CTS Timing repair
            {self.report_num_instances}

            repair_timing -setup -setup_margin {setup_margin}
            repair_timing -hold -setup_margin {setup_margin} -hold_margin {hold_margin} -max_buffer_percent {hold_max_buffer_percent}  -allow_setup_violations

            set_placement_padding -global -left {padding_final} -right {padding_final}

            detailed_placement

            optimize_mirroring

            estimate_parasitics -placement

            {self.write_reports(prefix='cts_rsz')}
            """)
        return True


    def add_fillers(self) -> bool:
        self.check_detailed_placement()
        """add decap and filler cells"""
        decaps = self.technology.get_special_cell_by_type(CellType.Decap)
        stdfillers = self.technology.get_special_cell_by_type(CellType.StdFiller)

        fill_cells = []
        if len(decaps) == 0:
            self.logger.info("The technology plugin 'special cells: decap' field does not exist. It should specify a list of decap cells. Filling with stdfiller instead.")
        else:
            # Decap cells as fillers
            fill_cells += list(map(lambda c: str(c), decaps[0].name))

        if len(stdfillers) == 0:
            self.logger.warning("The technology plugin 'special cells: stdfiller' field does not exist. It should specify a list of (non IO) filler cells. No filler will be added. You can override this with an add_fillers hook if you do not specify filler cells in the technology plugin.")
        else:
            # Then the rest is stdfillers
            fill_cells += list(map(lambda c: str(c), stdfillers[0].name))

            self.block_append(f"""
            ################################################################
            # Filler cell insertion

            set_propagated_clock [all_clocks]

            filler_placement {{ {' '.join(fill_cells)} }}

            """)
        return True

    @property
    def global_route_cmd(self) -> str:
        cmd = f"""
        global_route -guide_file {self.route_guide_path} -congestion_iterations 150 -verbose -congestion_report_file {self.run_dir}/congestion.rpt
        estimate_parasitics -global_routing
        """
        return cmd

    def global_route(self) -> bool:
        self.check_detailed_placement()
        routing_adj = self.get_setting('par.openroad.global_route.routing_adjustment')
        metals=self.get_stackup().metals[1:]
        idx_clock_bottom_metal=min(2,len(metals)-1)

        self.block_append(f"""
        ################################################################
        # Global routing
        # reduce the routing resources of all routing layers by X%
        set_global_routing_layer_adjustment {metals[0].name}-{metals[-1].name} {routing_adj}
        set_routing_layers -signal {metals[0].name}-{metals[-1].name} -clock {metals[idx_clock_bottom_metal].name}-{metals[-1].name}

        # hard-coded in the example OpenROAD scripts
        # set_macro_extension 2

        {self.global_route_cmd}
        """)
        return True


    def global_route_resize(self) -> bool:
        if self.timing_driven:
            routing_adj = self.get_setting('par.openroad.global_route_resize.routing_adjustment')
            metals=self.get_stackup().metals[1:]
            hold_margin = self.get_setting('par.openroad.global_route_resize.hold_margin')


            self.block_append(f"""
            ###########################
            # Post-GRT Timing repair

            remove_fillers

            set_global_routing_layer_adjustment {metals[0].name}-{metals[-1].name} {routing_adj}
            repair_timing -hold -hold_margin {hold_margin} -allow_setup_violations

            detailed_placement

            # post-timing optimizations STA
            estimate_parasitics -global_routing
            """)
            self.add_fillers()
            self.block_append(f"""
            {self.global_route_cmd}
            {self.write_reports(prefix='grt_rsz')}
            """)
        return True


    def detailed_route(self) -> bool:
        metals=self.get_stackup().metals[1:]

        self.block_append(f"""
        ################################################################
        # Detailed routing

        set_propagated_clock [all_clocks]

        set_thread_count {self.get_setting('vlsi.core.max_threads')}

        # NOTE: many other arguments available
        detailed_route \\
            -bottom_routing_layer {metals[0].name} \\
            -top_routing_layer {metals[-1].name} \\
            -output_drc {self.run_dir}/{self.top_module}_route_drc.rpt \\
            -output_maze {self.run_dir}/{self.top_module}_maze.log \\
            -save_guide_updates \\
            -verbose 1
        """)
        return True

    def read_spef(self) -> str:
        cmds = ["# Read Spef for OpenSTA"]
        # openroad doesn't support writing SPEFs for different corners
        spef_path = self.output_spef_paths[0]
        for corner in self.corner_names:
            cmds.append(f"read_spef -corner {corner} {spef_path}")
        return '\n'.join(cmds)

    def extraction(self) -> bool:
        spef_path = self.output_spef_paths[0]
        self.block_append(f"""
        ################################################################
        # Extraction
        define_process_corner -ext_model_index 0 X
        """)

        corners = self.get_mmmc_corners()
        corner_cnt = len(corners) if corners else 1
        for openrcx_file in self.get_setting('par.openroad.openrcx_techfiles'):
            self.block_append(f"extract_parasitics -ext_model_file {openrcx_file} -corner_cnt {corner_cnt}")

        self.block_append(f"""
        write_spef {spef_path}

        # Read Spef for OpenSTA
        {indent(self.read_spef(), prefix=2*4*' ').strip()}
        """)

        return True


    # Copy and hack the klayout techfile, to add all required LEFs
    def setup_klayout_techfile(self) -> str:
        source_path = Path(self.get_setting('par.openroad.klayout_techfile_source'))
        klayout_techfile_filename = os.path.basename(source_path)
        if not source_path.exists():
            # self.logger.error(f"Klayout techfile not specified in tech plugin or doesn't exist. Klayout won't be able to write GDS file. (par.openroad.klayout_techfile_source: {source_path})")
            raise FileNotFoundError(f"Klayout techfile not specified in tech plugin or doesn't exist. Klayout won't be able to write GDS file. ('par.openroad.klayout_techfile_source': {source_path})")

        cache_tech_dir_path = Path(self.technology.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / klayout_techfile_filename
        klayout_techfile_path = dest_path

        # klayout needs all lefs
        tech_lib_lefs = self.technology.read_libs([hammer_tech.filters.lef_filter], hammer_tech.HammerTechnologyUtils.to_plain_item, self.tech_lib_filter())
        extra_lib_lefs = self.technology.read_libs([hammer_tech.filters.lef_filter], hammer_tech.HammerTechnologyUtils.to_plain_item, self.extra_lib_filter())

        insert_lines=''
        for lef_file in tech_lib_lefs+extra_lib_lefs:
            insert_lines += f"<lef-files>{lef_file}</lef-files>\n"

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying Klayout Techfile: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    if "<lef-files>merged.lef</lef-files>" in line:
                        continue
                    if '<no-zero-length-paths>' in line:
                        """ we want to disallow zero length paths (i.e. convert to a polygon instead)
                            otherwise calibre throws an error during DRC/LVS
                            but setting this flag to 'true' doesn't seem to work
                        """
                        line = line.replace('<no-zero-length-paths>false','<no-zero-length-paths>true')
                    if '</lefdef>' in line:
                        df.write(insert_lines)
                    df.write(line)
        return str(klayout_techfile_path)


    def write_gds(self) -> str:
        cmds: List[str] = []

        klayout_techfile_path = self.setup_klayout_techfile()


        gds_files = self.technology.read_libs([
            hammer_tech.filters.gds_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_gds = list(map(lambda ilm: ilm.gds, self.get_input_ilms()))
            gds_files.extend(ilm_gds)

        layer_map_file=self.get_setting('par.inputs.gds_map_file')

        # the first entry of $KLAYOUT_PATH will be the one where the configuration is stored when KLayout exits
        #   otherwise KLayout tries to write everything to the same directory as the klayout binary and throws an error if it is not writeable
        klayout_path = os.path.join(self.run_dir, 'klayout')
        os.makedirs(klayout_path, exist_ok=True)
        os.environ['KLAYOUT_PATH'] = klayout_path

        def2stream_file = Path(self.get_setting('par.openroad.def2stream_file'))
        if not def2stream_file.exists():
            raise FileNotFoundError(f"Def2stream Python script not found for Klayout not specified in openroad plugin or doesn't exist. Klayout won't be able to write GDS file. ('par.openroad.def2stream_file': {def2stream_file})")
        def2stream_file = self.get_setting('par.openroad.def2stream_file')

        klayout_bin = self.get_setting('par.openroad.klayout_bin')
        self.block_tcl_append(f"""
        # write DEF (need this to write GDS)
        write_def {self.output_def_filename}

        # write gds
        # klayout args explained: https://www.klayout.de/command_args.html
        set in_files {{ {" ".join(gds_files)} }}
        exec {klayout_bin} -rd out_file={self.output_gds_filename} \\
                -zz -d 40 \\
                -rd design_name={self.top_module} \\
                -rd in_def={self.output_def_filename} \\
                -rd in_files=$in_files \\
                -rd config_file= \\
                -rd seal_file= \\
                -rd tech_file={klayout_techfile_path} \\
                -rd layer_map={layer_map_file} \\
                -rm {def2stream_file}
        """, cmds, clean=False, verbose=False)
        return '\n'.join(cmds).strip()


    def write_sdf(self) -> str:
        cmds = [""]
        # are multiple corners necessary? Tempus only supports reading one SDF
        self.block_tcl_append(f"""
        write_sdf -corner setup -gzip {self.output_sdf_path}
        """, cmds, clean=False, verbose=False)
        return '\n'.join(cmds).strip()


    def write_regs(self) -> bool:
        # TODO: currently no analagous OpenROAD default script
        return True
    
    def write_reports(self, prefix: str) -> str:
        if self.get_setting('par.openroad.write_reports') and self.timing_driven:
            return f"write_reports {prefix}"
        else:
            return ""

    @property
    def write_reports_tcl(self) -> str:
        return os.path.join(self.run_dir, "write_reports.tcl")


    def generate_report(self, cmd: str, rpt_name: str, output_buffer: List[str]) -> bool:
        self.tcl_append(f'puts "(hammer: begin_report > {self.reports_path(rpt_name)})"', output_buffer)
        self.block_tcl_append(cmd, output_buffer, clean=True)
        self.tcl_append(f'puts "(hammer: end_report)"\n', output_buffer)
        return True

    def create_write_reports_tcl(self) -> List[str]:
        '''
        Creates the write_repors.tcl command that is sourced at the beginning of an OpenROAD session,
            and is called with the command "write_reports <prefix>"
        Output report info with header and footer, to be read by the log_to_reports() function
            and written to the appropriate report file after OpenROAD completes.
        The <cmd>_metric(s) commands tells OpenROAD to dump this metric into the JSON 
            file specified by the -metrics flag in the tool invocation (see self.metrics_file)
        '''
        # NOTE: both report_check_types and report_power commands have [> filename] option but it just generates an empty file...
        write_reports_cmds = [""]
        prefix = "${prefix}"
        self.block_tcl_append("""
        ################################################################
        # Write Reports Function
        proc write_reports { prefix } {
        """, write_reports_cmds, clean=True, verbose=False)

        self.generate_report("report_check_types -max_slew -max_capacitance -max_fanout -violators -digits 3",
            f"{prefix}_sta.check_types.slew_cap_fanout.rpt", write_reports_cmds)

        self.generate_report("report_check_types -max_delay -max_skew -digits 3",
            f"{prefix}_sta.check_types.delay_skew.rpt", write_reports_cmds)

        group_count = 200
        for corner in ['setup', 'hold']:
            path_delay = 'max' if corner == 'setup' else 'min'
            self.generate_report(f"report_checks -sort_by_slack -path_delay {path_delay} -fields {{slew cap input nets fanout}} -format full_clock_expanded -group_count {group_count} -corner {corner}",
                f"{prefix}_sta.checks.{path_delay}.{corner}.rpt", write_reports_cmds)

        self.generate_report(f"report_checks -sort_by_slack -unconstrained -fields {{slew cap input nets fanout}} -format full_clock_expanded -group_count {group_count}",
            f"{prefix}_sta.checks.unconstrained.rpt", write_reports_cmds)

        self.generate_report(f"""
        report_units
        report_units_metric
        report_tns -digits 3
        report_tns_metric -setup
        report_tns_metric -hold
        report_wns -digits 3
        report_worst_negative_slack_metric -setup
        report_worst_negative_slack_metric -hold
        report_worst_slack -max -digits 3
        report_worst_slack -min -digits 3
        report_worst_slack_metric -setup
        report_worst_slack_metric -hold
        report_clock_skew -digits 3
        report_clock_skew_metric
        """, f"{prefix}_sta.summary.rpt", write_reports_cmds)

        self.generate_report("report_floating_nets -verbose",
            f"{prefix}_sta.floating_nets.rpt", write_reports_cmds)

        self.generate_report(f"""
        report_design_area
        report_design_area_metrics
        {self.report_num_instances}
        """, f"{prefix}_sta.util.rpt", write_reports_cmds)

        report_power = ""
        for corner in self.corner_names:
            report_power += f"""
            report_power -corner {corner} -digits 3
            report_power_metric -corner {corner}
            """
        self.generate_report(report_power, f"{prefix}_sta.power.rpt", write_reports_cmds)

        self.tcl_append("}\n", write_reports_cmds)

        return write_reports_cmds

    def log_to_reports(self) -> bool:
        ''' Parse OpenROAD log to create reports
        '''
        if not self.get_setting('par.openroad.write_reports'):
            return True
        with open(self.openroad_log,'r') as f:
            writing_rpt = False
            rpt: List[str] = []
            rpt_name = ""
            for line in f:
                if line.startswith('(hammer: end_report'):
                    writing_rpt = False
                    if rpt_name != "":
                        with open(rpt_name,'w') as fw:
                            fw.write(''.join(rpt))
                    else:
                        self.logger.error("Report name not found!")
                    rpt = []
                if writing_rpt:
                    rpt.append(line)
                if line.startswith('(hammer: begin_report'):
                    writing_rpt = True
                    match = re.match(r"^.*begin_report > (.*)\)",line)
                    if match:
                        rpt_name = match.group(1)
        return True


    def write_design(self) -> bool:

        phys_cells_str = " ".join(self.get_physical_only_cells())

        self.block_append(f"""
        ################################################################
        # Write Design

        {self.write_reports(prefix='rcx')}

        # Ensure all OR created (rsz/cts) instances are connected
        global_connect

        # write netlist
        write_verilog -remove_cells {{ {phys_cells_str} }} -include_pwr_gnd {self.output_netlist_filename}

        # write sim netlist
        write_verilog -remove_cells {{ {phys_cells_str} }} {self.output_sim_netlist_filename}

        # GDS streamout.
        {self.write_gds()}

        # Write SDF
        {self.write_sdf()}

        """)

        # TODO: look at IR drop analysis from ~OpenROAD-flow-scripts/flow/scripts/final_report.tcl
        # Static IR drop analysis

        # # Make sure that generated-scripts exists.
        # os.makedirs(self.generated_scripts_dir, exist_ok=True)

        self.ran_write_design=True
        return True


    def generate_make_tracks_tcl(self) -> str:
        output = []
        # initialize_floorplan removes existing tracks
        #   --> use the make_tracks command to add routing tracks
        #       to a floorplan (with no arguments it uses default from tech LEF)
        layers = self.get_setting('par.generate_power_straps_options.by_tracks.strap_layers')
        for metal in self.get_stackup().metals:
            # TODO: might need separate x/y pitch definition in stackup
            output.append(f"make_tracks {metal.name} -x_offset {metal.offset} -x_pitch {metal.pitch} -y_offset {metal.offset} -y_pitch {metal.pitch}")
        return "\n".join(output)


    @property
    def floorplan_mode(self) -> str:
        return str(self.get_setting('par.openroad.floorplan_mode'))


    def create_floorplan_tcl(self) -> List[str]:
        """
        Create a floorplan TCL depending on the floorplan mode.
        """
        output = []  # type: List[str]

        if self.floorplan_mode == "manual":
            floorplan_script_contents = str(self.get_setting('par.openroad.floorplan_script_contents'))
            output.append("# Floorplan manually specified from HAMMER")
            output.extend(floorplan_script_contents.split("\n"))
        elif self.floorplan_mode == "generate" or self.floorplan_mode == "auto_macro":
            output.extend(self.generate_floorplan_tcl())
        elif self.floorplan_mode == "auto":
            # NOT SUPPORTED
            pass
        else:
            if self.floorplan_mode != "blank":
                self.logger.error("Invalid floorplan_mode {mode}. Using blank floorplan.".format(mode=self.floorplan_mode))
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

    def rotate_coordinates_old(self, origin: Tuple[Decimal, Decimal], size: Tuple[Decimal, Decimal], orientation: str) -> Tuple[Decimal, Decimal]:
        x,y = origin
        width,height = size
        if orientation == 'r0':
            return (x,y)
        elif orientation == 'r90':
            return (x+height,y)
        elif orientation == 'r180':
            return (x+width,y+height)
        elif orientation == 'r270':
            return (x,y+width)
        elif orientation == 'mx':
            return (x,y+height)
        elif orientation == 'my':
            return (x+width,y)
        elif orientation == 'mx90':
            return (x,y)
        elif orientation == 'my90':
            return (x+height,y+width)
        else:
            self.logger.error(f"Invalid orientation {orientation}")
            return (x,y)
    
    def rotate_coordinates(self, origin: Tuple[Decimal, Decimal], orientation: str) -> Tuple[str, str]:
        # TODO: need to figure out origin translations for rotations besides R90/R270
        x = str(origin[0])
        y = str(origin[1])
        if orientation == 'r0':
            return (x,y)
        elif orientation == 'r90':
            return (f"[expr {x} + $height - $origin_y]",
                    f"[expr {y} + $origin_x]")
        elif orientation == 'r180':
            return (f"[expr {x} + $width]",
                    f"[expr {y} + $height]")
        elif orientation == 'r270':
            return (f"[expr {x} + $origin_y]",
                    f"[expr {y} + $width - $origin_x]")
        elif orientation == 'mx':
            return (x,
                    f"[expr {y} + $height]")
        elif orientation == 'my':
            return (f"[expr {x} + $width]",
                    y)
        elif orientation == 'mx90':
            return (x,y)
        elif orientation == 'my90':
            return (f"[expr {x} + $height]",
                    f"[expr {y} + $width]")
        else:
            self.logger.error(f"Invalid orientation {orientation}")
            return (x,y)

    def convert_orientation_hammer2openroad(self, orientation) -> str:
        # None case
        orientation = orientation if orientation is not None else "r0"
        # openroad names orientations differently from hammer
        #   hammer:   r0|r90|r180|r270|mx|my|mx90 |my90
        #   openroad: R0|R90|R180|R270|MX|MY|MXR90|MYR90
        openroad_orientation = orientation.upper()
        if orientation == "mx90":
            openroad_orientation = "MXR90"
        elif orientation == "my90":
            openroad_orientation = "MYR90"
        return openroad_orientation

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
        global_top_layer = self.get_setting('par.blockage_spacing_top_layer') #  type: Optional[str]
        floorplan_origin_pos = self.get_setting('par.openroad.floorplan_origin_pos')

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
                self.block_tcl_append(chip_size_constraint, output)
            elif self.floorplan_mode == 'generate':

                if constraint.create_physical:
                    pass
                if constraint.type == PlacementConstraintType.Dummy:
                    pass
                elif constraint.type == PlacementConstraintType.Placement:
                    pass
                # for OpenROAD
                elif constraint.type in [PlacementConstraintType.HardMacro, PlacementConstraintType.Hierarchical]:
                    x,y = constraint.x, constraint.y
                    orientation = constraint.orientation if constraint.orientation else 'r0'
                    x_expr = str(x)
                    y_expr = str(y)
                    if floorplan_origin_pos == 'bottom_left':
                        x_expr,y_expr = self.rotate_coordinates( (constraint.x,constraint.y), orientation )
                    orientation = self.convert_orientation_hammer2openroad(orientation)
                    inst_name=new_path

                    floorplan_cmd = f"""place_cell -inst_name {inst_name} -orient {orientation} -origin $origin -status FIRM"""

                    self.block_tcl_append(f"""
                    set inst [[ord::get_db_block] findInst {inst_name}]
                    # only place macro if it is present in design
                    if {{$inst == "NULL"}} {{
                        puts "(WARNING) Cell/macro {inst_name} not found!"
                    }} else {{
                        set inst_master [$inst getMaster]
                        # TODO: can we not hard-code 1000? get units somehow?
                        set width [expr [$inst_master getWidth] / 1000]
                        set height [expr [$inst_master getHeight] / 1000]
                        set origin [$inst_master getOrigin]
                        set origin_x [expr [lindex $origin 0] / 1000]
                        set origin_y [expr [lindex $origin 1] / 1000]
                        set x {x_expr}
                        set y {y_expr}
                        set origin "$x $y"
                        puts "(hammer) {floorplan_cmd}"
                        {floorplan_cmd}
                    }}
                    """, output, clean=True, verbose=False)

                    spacing = self.get_setting('par.blockage_spacing')

                    # TODO: find equivalent for place/route halo in OpenROAD

                elif constraint.type == PlacementConstraintType.Obstruction:
                    # TODO: can OpenROAD even do this?!
                    pass
                else:
                    assert False, "Should not reach here"
        return output


    def specify_std_cell_power_straps(self, blockage_spacing: Decimal, bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        """
        Generate a list of TCL commands that build the low-level standard cell power strap rails.
        This will use the -master option to create power straps based on technology.core.tap_cell_rail_reference.
        The layer is set by technology.core.std_cell_rail_layer, which should be the highest metal layer in the std cell rails.
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power net names (e.g. ["VDD", "VSS"]). Currently only two are supported.
        :return: A list of TCL commands that will generate power straps on rails.
        """
        layer_name = self.get_setting('technology.core.std_cell_rail_layer')
        layer = self.get_stackup().get_metal(layer_name)
        # core_site_height = self.technology.config.sites[0].y
        width = 2*layer.min_width
        # pitch = 2*core_site_height  # since power/gnd rails alternate
        tcl=[]
        # followpins indicates that the stripe forms part of the stdcell rails, pitch and spacing are dictated by the stdcell rows, the -width is not needed if it can be determined from the cells
        tcl.append(f"add_pdn_stripe -grid {{grid}} -layer {{{layer.name}}} -width {width} -offset 0 -followpins\n")
        #  -pitch {pitch}
        return tcl

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
        pins_tcl = "-extend_to_boundary" if (add_pins) else ""
        tcl = [f"add_pdn_stripe -grid {{grid}} -layer {{{layer_name}}} -width {width} -pitch {pitch} -offset {offset} -spacing {spacing} {pins_tcl}\n"]
        return tcl

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
