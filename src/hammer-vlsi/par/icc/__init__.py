#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer-vlsi plugin for Synopsys ICC.
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

import os
from shutil import copyfile
from os.path import dirname

from hammer_vlsi import HammerPlaceAndRouteTool
from hammer_vlsi import SynopsysTool
from hammer_vlsi import HammerVLSILogging

class ICC(HammerPlaceAndRouteTool, SynopsysTool):
    def do_run(self) -> bool:
        # Locate reference methodology tarball.
        synopsys_rm_tarball = self.get_synopsys_rm_tarball("ICC")

        # Generate 'enter' fragment for use in scripts like open_chip.
        with open(os.path.join(self.run_dir, "enter"), "w") as f:
            f.write("""
export ICC_HOME="{icc_home}"
export PATH="{icc_dir}:$PATH"
export MGLS_LICENSE_FILE="{mgls}"
export SNPSLMD_LICENSE_FILE="{snps}"
""".format(
            icc_home=dirname(dirname(self.get_setting("par.icc.icc_bin"))),
            icc_dir=os.path.dirname(self.get_setting("par.icc.icc_bin")),
            mgls=self.get_setting("synopsys.MGLS_LICENSE_FILE"),
            snps=self.get_setting("synopsys.SNPSLMD_LICENSE_FILE")
))

#~ if [[ "$icv" != "" ]]
#~ then
#~ cat >>"$run_dir"/enter <<EOF
#~ export ICV_HOME_DIR="$(dirname $(dirname $(dirname $icv)))"
#~ export PATH="$(dirname $icv):\$PATH"
#~ EOF
#~ fi

        # Pre-extract the Synopsys reference methodology for ICC.
        self.run_executable([
            "tar", "-xf", synopsys_rm_tarball, "-C", self.run_dir, "--strip-components=1"
        ])

        # Make sure that generated-scripts exists.
        generated_scripts_dir = os.path.join(self.run_dir, "generated-scripts")
        os.makedirs(generated_scripts_dir, exist_ok=True)

#~ if [[ "$icv" == "" ]]
#~ then
    #~ echo "ICV is not specified" >&2
    #~ # exit 1
#~ fi


#~ # Copy over any resource files if needed.
#~ resources_icc_path="$($get_config $config_db -n "" par.icc.resources_icc_path)"
#~ resources_tech_path="$($get_config $config_db -n "" par.icc.resources_tech_path)"
#~ resources_project_path="$($get_config $config_db -n "" par.icc.resources_project_path)"
#~ if [[ ! -z "$resources_icc_path" ]]; then
    #~ cp -ra "${resources_icc_path}"/* $run_dir
#~ fi
#~ if [[ ! -z "$resources_tech_path" ]]; then
    #~ cp -ra "${resources_tech_path}"/* $run_dir
#~ fi
#~ if [[ ! -z "$resources_project_path" ]]; then
    #~ cp -ra "${resources_project_path}"/* $run_dir
#~ fi

        # Gather/load libraries.
        timing_dbs = ' '.join(self.read_libs([self.timing_db_filter], self.to_plain_item))
        milkyway_lib_dirs = ' '.join(self.read_libs([self.milkyway_lib_dir_filter], self.to_plain_item))
        milkyway_techfiles = ' '.join(self.read_libs([self.milkyway_techfile_filter], self.to_plain_item))
        tlu_max_caps = ' '.join(self.read_libs([self.tlu_max_cap_filter], self.to_plain_item))
        tlu_min_caps = ' '.join(self.read_libs([self.tlu_min_cap_filter], self.to_plain_item))

        if timing_dbs == "":
            self.logger.error("No timing dbs (libs) specified!")
            return False
        if milkyway_lib_dirs == "":
            self.logger.error("No milkyway lib dirs specified!")
            return False
        if milkyway_techfiles == "":
            self.logger.error("No milkyway tech files specified!")
            return False
        if tlu_max_caps == "" and tlu_min_caps == "":
            self.logger.error("No tlu+ cap files specified!")
            return False

        # Load input files.
        verilog_args = list(self.input_files)
        error = False
        for v in verilog_args:
            if not (v.endswith(".v")):
                self.logger.error("Non-verilog input {0} detected! ICC only supports Verilog for its netlists.".format(v))
                error = True
            if not os.path.isfile(v):
                self.logger.error("Input file {0} does not exist!".format(v))
                error = True
        if error:
            return False

        if len(verilog_args) < 1:
            self.logger.error("No post-synthesis Verilog netlists specified!")
            return False

        verilogs = ' '.join(verilog_args)

        # Start customizing the reference methodology.
        # Set all the input files, etc.
        with open(os.path.join(self.run_dir, "rm_setup", "common_setup.tcl"), "a") as f:
            f.write("""
set DESIGN_NAME "{top_module}";
set RTL_SOURCE_FILES "{verilogs}";
set TARGET_LIBRARY_FILES "{timing_dbs}";
set MW_REFERENCE_LIB_DIRS "{milkyway_lib_dirs}";
set MIN_LIBRARY_FILES "";
set TECH_FILE "{milkyway_techfiles}";
set TLUPLUS_MAX_FILE "{tlu_max_caps}";
set TLUPLUS_MIN_FILE "{tlu_min_caps}";
set ALIB_DIR "alib";
set DCRM_CONSTRAINTS_INPUT_FILE "generated-scripts/constraints.tcl";
set REPORTS_DIR "reports";
set RESULTS_DIR "results";
set CLOCK_UNCERTAINTY "0.04";
set INPUT_DELAY "0.10";
set OUTPUT_DELAY "0.10";
set ICC_NUM_CORES {num_cores};
set_host_options -max_cores {num_cores};

set MW_POWER_NET                "{MW_POWER_NET}";
set MW_POWER_PORT               "{MW_POWER_PORT}";
set MW_GROUND_NET               "{MW_GROUND_NET}";
set MW_GROUND_PORT              "{MW_GROUND_PORT}";
""".format(
                top_module=self.top_module,
                verilogs=verilogs,
                timing_dbs=timing_dbs,
                milkyway_lib_dirs=milkyway_lib_dirs,
                num_cores=self.get_setting("vlsi.core.max_threads"),
                milkyway_techfiles=milkyway_techfiles,
                tlu_max_caps=tlu_max_caps,
                tlu_min_caps=tlu_min_caps,
                MW_POWER_NET=self.get_setting("par.icc.MW_POWER_NET"),
                MW_POWER_PORT=self.get_setting("par.icc.MW_POWER_PORT"),
                MW_GROUND_NET=self.get_setting("par.icc.MW_GROUND_NET"),
                MW_GROUND_PORT=self.get_setting("par.icc.MW_GROUND_PORT")
            ))

        icc_setup_path = os.path.join(self.run_dir, "rm_setup", "icc_setup.tcl")
        common_setup_path = os.path.join(self.run_dir, "rm_setup", "common_setup.tcl")

        common_setup_appendix_tcl_path = str(self.get_setting("par.icc.common_setup_appendix_tcl_path", nullvalue=""))
        if common_setup_appendix_tcl_path != "":
            with open(common_setup_appendix_tcl_path, "r") as f:
                common_setup_appendix_tcl_path_contents = str(f.read()).split("\n")  # type: List[str]
            # TODO(edwardw): come up with a more generic "source locator" for hammer
            header_text = "# The following snippet was added by HAMMER from {path}".format(
                path=common_setup_appendix_tcl_path)
            common_setup_appendix_tcl_path_contents.insert(0, header_text)
            with open(common_setup_path, "a") as f:
                f.write("\n".join(common_setup_appendix_tcl_path_contents))

        icc_setup_appendix_tcl_path = str(self.get_setting("par.icc.icc_setup_appendix_tcl_path", nullvalue=""))
        if icc_setup_appendix_tcl_path != "":
            with open(icc_setup_appendix_tcl_path, "r") as f:
                icc_setup_appendix_tcl_path_contents = str(f.read()).split("\n")  # type: List[str]
            # TODO(edwardw): come up with a more generic "source locator" for hammer
            header_text = "# The following snippet was added by HAMMER from {path}".format(
                path=icc_setup_appendix_tcl_path)
            icc_setup_appendix_tcl_path_contents.insert(0, header_text)
            with open(icc_setup_path, "a") as f:
                f.write("\n".join(icc_setup_appendix_tcl_path_contents))

#~ # Read the core's configuration file to figure out what all the clocks should
#~ # look like.
#~ cat >> $run_dir/generated-scripts/constraints.tcl <<"EOF"
#~ if {![info exists generated_scripts_constraints_included]} {
#~ set generated_scripts_constraints_included 1;
#~ EOF

#~ python3 >>$run_dir/generated-scripts/constraints.tcl <<EOF
#~ import json
#~ with open("${config}") as f:
    #~ config = json.load(f)

#~ import re
#~ for clock in config["clocks"]:
    #~ clock_name = clock["name"]
    #~ clock_period = clock["period"]
    #~ par_derating = clock["par derating"]
    #~ if not re.match("[0-9]+ *[np]s", clock_period):
        #~ error
    #~ if not re.match("[0-9]+ *[np]s", par_derating):
        #~ error

    #~ if re.match("[0-9]+ *ns", clock_period):
        #~ clock_period_ns = re.sub(" *ns", "", clock_period)
    #~ if re.match("[0-9]+ *ps", clock_period):
        #~ clock_period_ns = int(re.sub(" *ps", "", clock_period)) / 1000.0

    #~ if re.match("[0-9]+ *ns", par_derating):
        #~ par_derating_ns = re.sub(" *ns", "", par_derating)
    #~ if re.match("[0-9]+ *ps", par_derating):
        #~ par_derating_ns = int(re.sub(" *ps", "", par_derating)) / 1000.0

    #~ print("create_clock {0} -name {0} -period {1}".format(clock_name, clock_period_ns + par_derating_ns))
    #~ print("set_clock_uncertainty 0.01 [get_clocks {0}]".format(clock_name))
#~ EOF

#~ # The constraints file determines how the IO is constrained and what the clocks
#~ # look like.
#~ cat >> $run_dir/generated-scripts/constraints.tcl <<"EOF"
#~ # set drive strength for inputs
#~ #set_driving_cell -lib_cell INVD0BWP12T [all_inputs]
#~ # set load capacitance of outputs
#~ set_load -pin_load 0.004 [all_outputs]

#~ #set all_inputs_but_clock [remove_from_collection [all_inputs] [get_ports clock]]
#~ #set_input_delay 0.02 -clock [get_clocks clock] $all_inputs_but_clock
#~ #set_output_delay 0.03 -clock [get_clocks clock] [all_outputs]

#~ #set_isolate_ports [all_outputs] -type buffer
#~ #set_isolate_ports [remove_from_collection [all_inputs] clock] -type buffer -force
#~ EOF

#~ # We allow users to specify metal routing directions since some technologies
#~ # don't support those.
#~ python3 >>$run_dir/generated-scripts/constraints.tcl <<EOF
#~ import json
#~ with open("${technology}") as f:
    #~ config = json.load(f)

#~ # Suppress PSYN-882 ("Warning: Consecutive metal layers have the same preferred routing direction") while the layer routing is being built.
#~ print("set suppress_errors  [concat \$suppress_errors  [list PSYN-882]]")

#~ for library in config["libraries"]:
    #~ if "metal layers" in library:
        #~ for layer in library["metal layers"]:
            #~ print("set_preferred_routing_direction -layers {{ {0} }} -direction {1}".format(layer["name"], layer["preferred routing direction"]))

#~ print("set suppress_errors  [lminus \$suppress_errors  [list PSYN-882]]")
#~ EOF

#~ cat >> $run_dir/generated-scripts/constraints.tcl <<"EOF"
#~ }
#~ # generated_scripts_constraints_included
#~ EOF

        # Use DC's Verilog output instead of the milkyway stuff, which requires
        # some changes to the RM.
        # FIXME: There's a hidden dependency on the SDC file here.
        self.replace_tcl_set("ICC_INIT_DESIGN_INPUT", "VERILOG", icc_setup_path)
        self.replace_tcl_set("ICC_IN_VERILOG_NETLIST_FILE", verilogs, icc_setup_path)
        #~ self.replace_tcl_set("ICC_IN_SDC_FILE", sdc_s, icc_setup_path)
        self.replace_tcl_set("ICC_FLOORPLAN_INPUT", "USER_FILE", icc_setup_path)
        self.replace_tcl_set("ICC_IN_FLOORPLAN_USER_FILE", "generated-scripts/floorplan.tcl", icc_setup_path)
        self.replace_tcl_set("ICC_NUM_CORES", self.get_setting("vlsi.core.max_threads"), icc_setup_path, quotes=False)

#~ # If there's no ICV then don't run any DRC stuff at all.
#~ if [[ "$icv" != "" ]]
#~ then
    #~ # ICC claims this is only necessary for 45nm and below, but I figure if anyone
    #~ # provides ICV metal fill rules then we might as well go ahead and use them
    #~ # rather than ICC's built-in metal filling.
    #~ if [[ "$metal_fill_ruleset" != "" ]]
    #~ then
        #~ sed 's@^set ADD_METAL_FILL.*@set ADD_METAL_FILL "ICV";@' -i $run_dir/rm_setup/icc_setup.tcl
        #~ sed "s@^set SIGNOFF_FILL_RUNSET .*@set SIGNOFF_FILL_RUNSET \"${metal_fill_ruleset[@]}\";@" -i $run_dir/rm_setup/icc_setup.tcl
    #~ fi

    #~ if [[ "$signoff_ruleset" != "" ]]
    #~ then
        #~ sed "s@^set SIGNOFF_DRC_RUNSET .*@set SIGNOFF_DRC_RUNSET \"${signoff_ruleset[@]}\";@" -i $run_dir/rm_setup/icc_setup.tcl
    #~ fi
#~ else
    #~ sed 's@^set ADD_METAL_FILL.*@set ADD_METAL_FILL "";@' -i $run_dir/rm_setup/icc_setup.tcl
#~ fi

#~ # The technology is expected to provide a list of filler cells that ICC uses.
#~ filler_metal_cells_list=$($list_macros -l $technology_macro_library -t "metal filler" | xargs echo)
#~ filler_cells_list=$($list_macros -l $technology_macro_library -t filler | xargs echo)
#~ sed 's@^set ADD_FILLER_CELL .*@set ADD_FILLER_CELL TRUE@' -i $run_dir/rm_setup/icc_setup.tcl
#~ sed "s@^set FILLER_CELL_METAL .*@set FILLER_CELL_METAL \"${filler_metal_cells_list}\";@" -i $run_dir/rm_setup/icc_setup.tcl
#~ sed "s@^set FILLER_CELL .*@set FILLER_CELL \"${filler_cells_list}\";@" -i $run_dir/rm_setup/icc_setup.tcl

#~ # I want ICC to run all the sanity checks it can
#~ sed "s@^set ICC_SANITY_CHECK.*@set ICC_SANITY_CHECK TRUE@" -i $run_dir/rm_setup/icc_setup.tcl

#~ # If I don't ask ICC for high-effort place/route then it does a bad job, so
#~ # just always ask for high effort.
#~ # FIXME: This should probably be a user tunable...
#~ sed 's@^set PLACE_OPT_EFFORT.*@set PLACE_OPT_EFFORT "high"@' -i $run_dir/rm_setup/icc_setup.tcl
#~ sed 's@^set ROUTE_OPT_EFFORT.*@set ROUTE_OPT_EFFORT "high"@' -i $run_dir/rm_setup/icc_setup.tcl
#~ sed 's@^set ICC_TNS_EFFORT_PREROUTE.*@set ICC_TNS_EFFORT_PREROUTE "HIGH"@' -i $run_dir/rm_setup/icc_setup.tcl
#~ sed 's@^set ICC_TNS_EFFORT_POSTROUTE.*@set ICC_TNS_EFFORT_POSTROUTE "HIGH"@' -i $run_dir/rm_setup/icc_setup.tcl

#~ # Some venders need the extra layer IDs.  While this is vendor-specific, I
#~ # don't see a reason to turn it off for everyone else.
#~ sed 's@^set MW_EXTENDED_LAYER_MODE.*@set MW_EXTENDED_LAYER_MODE TRUE@' -i $run_dir/rm_setup/icc_setup.tcl

#~ # For some reason, ICC isn't echoing some of my user input files.  I want it to.
#~ sed 's@source \$@source -echo $@g' -i $run_dir/rm_*/*.tcl

#~ # The only difference between this script and the actual ICC run is that this
#~ # one generates a list of macros that will be used to floorplan the design, while
#~ # the other one actually
#~ cat > $run_dir/generated-scripts/list_macros.tcl <<EOF
#~ source rm_setup/icc_setup.tcl
#~ open_mw_lib ${top}_LIB
#~ open_mw_cel -readonly init_design_icc

#~ create_floorplan -control_type aspect_ratio -core_aspect_ratio 1 -core_utilization 0.7 -left_io2core 3 -bottom_io2core 3 -right_io2core 3 -top_io2core 3 -start_first_row

#~ set top_left_x [lindex [get_placement_area] 0]
#~ set top_left_y [lindex [get_placement_area] 1]
#~ set bottom_right_x [lindex [get_placement_area] 2]
#~ set bottom_right_y [lindex [get_placement_area] 3]
#~ echo "${top} module=${top} top_left=(\$top_left_x, \$top_left_y) bottom_right=(\$bottom_right_x, \$bottom_right_y)" >> results/${top}.macros.out

#~ set fixed_cells [get_fp_cells -filter "is_fixed == true"]
#~ foreach_in_collection cell \$fixed_cells {
    #~ set full_name [get_attribute \$cell full_name]
    #~ set ref_name [get_attribute \$cell ref_name]
    #~ set height [get_attribute \$cell height]
    #~ set width [get_attribute \$cell width]
    #~ echo "\$full_name parent=${top} module=\$ref_name width=\$width height=\$height" >> results/${top}.macros.out
#~ }
#~ exit
#~ EOF

#~ ## FIXME: This throws errors because it's accessing some views on disk.
#~ ## I want ICC to try and fix DRCs automatically when possible.  Most of the
#~ ## commands are commented out for some reason, this enables them.
#~ #drc_runset="$(echo "${signoff_ruleset[@]}" | xargs basename -s .rs)"
#~ #sed 's@^set ICC_ECO_SIGNOFF_DRC_MODE .*@set ICC_ECO_SIGNOFF_DRC_MODE "AUTO_ECO"@' -i $run_dir/rm_setup/icc_setup.tcl
#~ #sed 's@.*#  s\(.*\)@s\1@' -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl
#~ #sed "s@^\\(signoff_autofix_drc .*\\)@exec $ICV_HOME_DIR/contrib/generate_layer_rule_map.pl -dplog signoff_drc_run/run_details/$drc_runset.dp.log -tech_file $(readlink -f ${tf[@]}) -o signoff_autofix_drc.config\n\\1@" -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl
#~ #sed 's@\$config_file@signoff_autofix_drc.config@' -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl

#~ # FIXME: I actually can't insert double vias on SAED32 becaues of DRC errors.
#~ # It smells like the standard cells just aren't setup for it, but this needs to
#~ # be fixed somehow as it'll be necessary for a real chip to come back working.
#~ sed 's@set ICC_DBL_VIA .*@set ICC_DBL_VIA FALSE@' -i $run_dir/rm_setup/icc_setup.tcl
#~ sed 's@set ICC_DBL_VIA_FLOW_EFFORT .*@set ICC_DBL_VIA_FLOW_EFFORT "NONE"@' -i $run_dir/rm_setup/icc_setup.tcl

        floorplan_mode = self.get_setting("par.icc.floorplan_mode")
        floorplan_script = self.get_setting("par.icc.floorplan_script")

        if floorplan_mode == "annotations":
            raise NotImplementedError("Not implemented")
        elif floorplan_mode == "manual":
        #~ cat >$run_dir/saed_32nm.tpl <<EOF
#~ template: m45_mesh(w1, w2) {
  #~ layer : M4 {
    #~ direction : vertical
    #~ width : @w1
    #~ pitch : 8
    #~ spacing : 1
    #~ offset :
  #~ }
  #~ layer : M5 {
    #~ direction : horizontal
    #~ width : @w2
    #~ spacing : 1
    #~ pitch : 8
    #~ offset :
  #~ }
#~ }
#~ EOF
            if floorplan_script == "null" or floorplan_script == "":
                self.logger.error("floorplan_mode is manual but no floorplan_script specified")
                return False
            copyfile(floorplan_script, os.path.join(self.run_dir, "generated-scripts", "floorplan_inner.tcl"))
        else:
            self.logger.error("Invalid floorplan_mode %s" % (floorplan_mode))
            return False

        # Prepend constraints to the floorplan.
        with open(os.path.join(self.run_dir, "generated-scripts", "floorplan.tcl"), "w") as f:
            f.write("""
source -echo -verbose generated-scripts/constraints.tcl
source -echo -verbose generated-scripts/floorplan_inner.tcl
""")

#~ # Opens the floorplan straight away, which is easier than doing it manually
#~ cat > $run_dir/generated-scripts/open_floorplan.tcl <<EOF
#~ source rm_setup/icc_setup.tcl
#~ open_mw_lib -r ${top}_LIB
#~ open_mw_cel -r floorplan
#~ EOF

#~ cat > $run_dir/generated-scripts/open_floorplan <<EOF
#~ cd $run_dir
#~ source enter
#~ $ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_floorplan.tcl
#~ EOF
#~ chmod +x $run_dir/generated-scripts/open_floorplan

#~ cat > $run_dir/generated-scripts/open_power.tcl <<EOF
#~ source rm_setup/icc_setup.tcl
#~ open_mw_lib -r ${top}_LIB
#~ open_mw_cel -r power
#~ EOF

#~ cat > $run_dir/generated-scripts/open_power <<EOF
#~ cd $run_dir
#~ source enter
#~ $ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_power.tcl
#~ EOF
#~ chmod +x $run_dir/generated-scripts/open_power

        with open(os.path.join(generated_scripts_dir, "open_chip.tcl"), "w") as f:
            f.write("""
source rm_setup/icc_setup.tcl
open_mw_lib -r {top}_LIB
open_mw_cel -r chip_finish_icc
""".format(top=self.top_module))

        with open(os.path.join(generated_scripts_dir, "open_chip"), "w") as f:
            f.write("""
cd {run_dir}
source enter
$ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_chip.tcl
""".format(run_dir=self.run_dir))
        self.run_executable([
            "chmod", "+x", os.path.join(generated_scripts_dir, "open_chip")
        ])

#~ # Write SDF
#~ cat > $run_dir/generated-scripts/write_sdf.tcl <<EOF
#~ source rm_setup/icc_setup.tcl
#~ open_mw_cel \$ICC_OUTPUTS_CEL -lib \$MW_DESIGN_LIBRARY
#~ current_design ${top}
#~ write_sdf \$RESULTS_DIR/\$DESIGN_NAME.output.sdf
#~ exit
#~ EOF

#~ cat > $run_dir/generated-scripts/write_sdf <<EOF
#~ cd $run_dir
#~ $ICC_HOME/bin/icc_shell -f generated-scripts/write_sdf.tcl
#~ EOF
#~ chmod +x $run_dir/generated-scripts/write_sdf

        # Build args.
        args = [
            os.path.join(self.tool_dir, "tools", "run-par"),
            "--run_dir", self.run_dir
            #~ "--dc", dc_bin,
            #~ "--MGLS_LICENSE_FILE", self.get_setting("synopsys.MGLS_LICENSE_FILE"),
            #~ "--SNPSLMD_LICENSE_FILE", self.get_setting("synopsys.SNPSLMD_LICENSE_FILE"),
            #~ "--preferred_routing_directions_fragment", preferred_routing_directions_fragment,
            #~ "--find_regs_tcl", os.path.join(self.tool_dir, "tools", "find-regs.tcl"),
            #~ "--top", self.top_module
        ]

        # Temporarily disable colours/tag to make DC run output more readable.
        # TODO: think of a more elegant way to do this?
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir) # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

tool = ICC()
