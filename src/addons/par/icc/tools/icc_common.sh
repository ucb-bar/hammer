#!/bin/bash
# Set up the environment to run ICC by extracting the Synopsys reference
# methodology, adding/modifying options, and generating scripts.
# Use with 'source'.
# You must set script_dir to the folder with the PLSI ICC scripts, typically
# src/addons/par/icc/tools.

unset run_dir
unset icc
unset rmtar
libs=()
mw=()
unset top
v=()
sdc=()
tlu_min=()
tlu_max=()
tf=()
unset find_regs
unset config
unset technology
unset floorplan_json
unset get_config
unset config_db
unset icv
metal_fill_ruleset=()
signoff_ruleset=()
unset technology_macro_library
unset pcad_pipe_list_macros
while [[ "$1" != "" ]]
do
    case "$1" in
    "$0") ;;
    --output_dir) run_dir="$2"; shift;;
    */icc_shell) icc="$1";;
    */icv64) icv="$1";;
    */ICC-RM_*.tar) rmtar="$1";;
    *.db) libs+=("$1");;
    */lib) mw+=("$(dirname "$1")");;
    --top) top="$2"; shift;;
    *.v) v+=("$1");;
    *.sdc) sdc+=("$1");;
    *Cmin.tluplus) tlu_min+=("$1");;
    *Cmax.tluplus) tlu_max+=("$1");;
    *rcbest.itf.tluplus) tlu_min+=("$1");;
    *rcworst.itf.tluplus) tlu_max+=("$1");;
    */FuncCmin/tluplus) tlu_min+=("$1");;
    */FuncCmax/tluplus) tlu_max+=("$1");;
    *mfill_rules.rs) metal_fill_ruleset+=("$1");;
    *drc_rules.rs) signoff_ruleset+=("$1");;
    *.tf) tf+=("$1");;
    */find-regs.tcl) find_regs="$1";;
    *.plsi_config.json) config="$1";;
    *.tech.json) technology="$1";;
    *.floorplan.json) floorplan_json="$1";;
    *get-config) get_config="$1";;
    *config.db.json) config_db="$1";;
    *.macro_library.json) technology_macro_library="$(readlink -f "$1")";;
    */pcad-pipe-list_macros) pcad_pipe_list_macros="$(readlink -f "$1")";;
    *) echo "Unknown argument $1"; exit 1;;
    esac
    shift
done

set -ex

# Directory containing ICC scripts.
# Should be something along the lines of src/addons/par/icc/tools
if [[ "$script_dir" == "" ]]; then
    echo "script_dir not set"
    exit 1
fi

rm -rf "$run_dir"
mkdir -p "$run_dir"

cat >"$run_dir"/enter <<EOF
export ICC_HOME="$(dirname $(dirname $icc))"
export PATH="$(dirname $icc):\$PATH"
export MGLS_LICENSE_FILE="$MGLS_LICENSE_FILE"
export SNPSLMD_LICENSE_FILE="$SNPSLMD_LICENSE_FILE"
EOF

if [[ "$icv" != "" ]]
then
cat >>"$run_dir"/enter <<EOF
export ICV_HOME_DIR="$(dirname $(dirname $(dirname $icv)))"
export PATH="$(dirname $icv):\$PATH"
EOF
fi
source "$run_dir"/enter

# Almost all of what I do is to just use Synopsys's reference methodology,
# which users are expected to have downloaded.
tar -xf "$rmtar" -C "$run_dir" --strip-components=1
mkdir -p $run_dir/generated-scripts

if [[ "${mw[@]}" == "" ]]
then
    echo "No milkyway libraries specified"
    exit 1
fi

for lib in "${mw[@]}"
do
    if test ! -d "$lib"
    then
        echo "Milkyway library $lib doesn't exist in filesystem" >&2
	exit 1
    fi
done

if [[ "${tlu_max[*]}" == "" || "${tlu_min[*]}" == "" ]]
then
    echo "No TLU+ files specified"
    exit 1
fi

if [[ "$PLSI_SCHEDULER_MAX_THREADS" == "" ]]
then
    export PLSI_SCHEDULER_MAX_THREADS="1"
fi

if [[ "${v[@]}" == "" ]]
then
    echo "No Verilog input provided" >&2
    exit 1
fi

if [[ "$icv" == "" ]]
then
    echo "ICV is not specified" >&2
    # exit 1
fi

if [[ "$get_config" == "" ]]
then
    echo "get-config not specified" >&2
    exit 1
fi

if [[ "$config_db" == "" ]]
then
    echo "config db not specified" >&2
    exit 1
fi

# Most of the customization of the reference methodology is done here: this
# sets all the input files and such.
mkdir -p $run_dir/rm_setup
cat >> $run_dir/rm_setup/common_setup.tcl <<EOF
set DESIGN_NAME "$top";
set RTL_SOURCE_FILES "$(readlink_array ${v[@]})";
set TARGET_LIBRARY_FILES "$(readlink_array ${libs[@]})";
set MW_REFERENCE_LIB_DIRS "$(readlink_array ${mw[@]})";
set MIN_LIBRARY_FILES "";
set TECH_FILE "$(readlink_array ${tf[@]})";
set TLUPLUS_MAX_FILE "$(readlink_array ${tlu_max[@]})";
set TLUPLUS_MIN_FILE "$(readlink_array ${tlu_min[@]})";
set ALIB_DIR "alib";
set DCRM_CONSTRAINTS_INPUT_FILE "generated-scripts/constraints.tcl";
set REPORTS_DIR "reports";
set RESULTS_DIR "results";
set CLOCK_UNCERTAINTY "0.04";
set INPUT_DELAY "0.10";
set OUTPUT_DELAY "0.10";
set ICC_NUM_CORES ${PLSI_SCHEDULER_MAX_THREADS};
set_host_options -max_cores ${PLSI_SCHEDULER_MAX_THREADS};

set MW_POWER_NET                "$($get_config $config_db -e par.icc.MW_POWER_NET)";
set MW_POWER_PORT               "$($get_config $config_db -e par.icc.MW_POWER_PORT)";
set MW_GROUND_NET               "$($get_config $config_db -e par.icc.MW_GROUND_NET)";
set MW_GROUND_PORT              "$($get_config $config_db -e par.icc.MW_GROUND_PORT)";
EOF

icc_setup_tcl_path=$($get_config $config_db -n "" par.icc.icc_setup_appendix_tcl_path)
if [[ "$icc_setup_appendix_tcl_path" != "" ]]
then
    echo "# The following snippet was added by PLSI from ${icc_setup_appendix_tcl_path}" >> $run_dir/rm_setup/icc_setup.tcl
    cat ${icc_setup_appendix_tcl_path} >> $run_dir/rm_setup/icc_setup.tcl
fi

# Read the core's configuration file to figure out what all the clocks should
# look like.
python3 >>$run_dir/generated-scripts/constraints.tcl <<EOF
import json
with open("${config}") as f:
	config = json.load(f)

import re
for clock in config["clocks"]:
	clock_name = clock["name"]
	clock_period = clock["period"]
	par_derating = clock["par derating"]
	if not re.match("[0-9]+ *[np]s", clock_period):
		error
	if not re.match("[0-9]+ *[np]s", par_derating):
		error

	if re.match("[0-9]+ *ns", clock_period):
		clock_period_ns = re.sub(" *ns", "", clock_period)
	if re.match("[0-9]+ *ps", clock_period):
		clock_period_ns = int(re.sub(" *ps", "", clock_period)) / 1000.0

	if re.match("[0-9]+ *ns", par_derating):
		par_derating_ns = re.sub(" *ns", "", par_derating)
	if re.match("[0-9]+ *ps", par_derating):
		par_derating_ns = int(re.sub(" *ps", "", par_derating)) / 1000.0

	print("create_clock {0} -name {0} -period {1}".format(clock_name, clock_period_ns + par_derating_ns))
	print("set_clock_uncertainty 0.01 [get_clocks {0}]".format(clock_name))
EOF

# The constraints file determines how the IO is constrained and what the clocks
# look like.
cat >> $run_dir/generated-scripts/constraints.tcl <<"EOF"
# set drive strength for inputs
#set_driving_cell -lib_cell INVD0BWP12T [all_inputs]
# set load capacitance of outputs
set_load -pin_load 0.004 [all_outputs]

#set all_inputs_but_clock [remove_from_collection [all_inputs] [get_ports clock]]
#set_input_delay 0.02 -clock [get_clocks clock] $all_inputs_but_clock
#set_output_delay 0.03 -clock [get_clocks clock] [all_outputs]

#set_isolate_ports [all_outputs] -type buffer
#set_isolate_ports [remove_from_collection [all_inputs] clock] -type buffer -force
EOF

# We allow users to specify metal routing directions since some technologies
# don't support those.
python3 >>$run_dir/generated-scripts/constraints.tcl <<EOF
import json
with open("${technology}") as f:
	config = json.load(f)

# Suppress PSYN-882 ("Warning: Consecutive metal layers have the same preferred routing direction") while the layer routing is being built.
print("set suppress_errors  [concat \$suppress_errors  [list PSYN-882]]")

for library in config["libraries"]:
	if "metal layers" in library:
		for layer in library["metal layers"]:
			print("set_preferred_routing_direction -layers {{ {0} }} -direction {1}".format(layer["name"], layer["preferred routing direction"]))

print("set suppress_errors  [lminus \$suppress_errors  [list PSYN-882]]")
EOF

# I want to use DC's Verilog output instead of the milkyway stuff, which
# requires some changes to the RM.
# FIXME: There's a hidden dependency on the SDC file here.
sed 's@^set ICC_INIT_DESIGN_INPUT.*@set ICC_INIT_DESIGN_INPUT "VERILOG";@' -i $run_dir/rm_setup/icc_setup.tcl
sed "s@^set ICC_IN_VERILOG_NETLIST_FILE.*@set ICC_IN_VERILOG_NETLIST_FILE \"${v[@]}\"@;" -i $run_dir/rm_setup/icc_setup.tcl
sed "s@^set ICC_IN_SDC_FILE.*@set ICC_IN_SDC_FILE \"${sdc[@]}\"@;" -i $run_dir/rm_setup/icc_setup.tcl
sed 's@^set ICC_FLOORPLAN_INPUT.*@set ICC_FLOORPLAN_INPUT "USER_FILE";@' -i $run_dir/rm_setup/icc_setup.tcl
sed 's@^set ICC_IN_FLOORPLAN_USER_FILE.*@set ICC_IN_FLOORPLAN_USER_FILE "generated-scripts/floorplan.tcl";@' -i $run_dir/rm_setup/icc_setup.tcl
sed "s@^set ICC_NUM_CORES.*@set ICC_NUM_CORES ${PLSI_SCHEDULER_MAX_THREADS};@" -i $run_dir/rm_setup/icc_setup.tcl

# If there's no ICV then don't run any DRC stuff at all.
if [[ "$icv" != "" ]]
then
    # ICC claims this is only necessary for 45nm and below, but I figure if anyone
    # provides ICV metal fill rules then we might as well go ahead and use them
    # rather than ICC's built-in metal filling.
    if [[ "$metal_fill_ruleset" != "" ]]
    then
        sed 's@^set ADD_METAL_FILL.*@set ADD_METAL_FILL "ICV";@' -i $run_dir/rm_setup/icc_setup.tcl
        sed "s@^set SIGNOFF_FILL_RUNSET .*@set SIGNOFF_FILL_RUNSET \"${metal_fill_ruleset[@]}\";@" -i $run_dir/rm_setup/icc_setup.tcl
    fi

    if [[ "$signoff_ruleset" != "" ]]
    then
        sed "s@^set SIGNOFF_DRC_RUNSET .*@set SIGNOFF_DRC_RUNSET \"${signoff_ruleset[@]}\";@" -i $run_dir/rm_setup/icc_setup.tcl
    fi
else
    sed 's@^set ADD_METAL_FILL.*@set ADD_METAL_FILL "";@' -i $run_dir/rm_setup/icc_setup.tcl
fi

# The technology is expected to provide a list of filler cells that ICC uses.
sed 's@^set ADD_FILLER_CELL .*@set ADD_FILLER_CELL TRUE@' -i $run_dir/rm_setup/icc_setup.tcl
sed "s@^set FILLER_CELL_METAL .*@set FILLER_CELL_METAL \"$($pcad_pipe_list_macros -l $technology_macro_library -t \"metal filler\" | xargs echo)\";@" -i $run_dir/rm_setup/icc_setup.tcl
sed "s@^set FILLER_CELL .*@set FILLER_CELL \"$($pcad_pipe_list_macros -l $technology_macro_library -t \"filler\" | xargs echo)\";@" -i $run_dir/rm_setup/icc_setup.tcl

# I want ICC to run all the sanity checks it can
sed "s@^set ICC_SANITY_CHECK.*@set ICC_SANITY_CHECK TRUE@" -i $run_dir/rm_setup/icc_setup.tcl

# If I don't ask ICC for high-effort place/route then it does a bad job, so
# just always ask for high effort.
# FIXME: This should probably be a user tunable...
sed 's@^set PLACE_OPT_EFFORT.*@set PLACE_OPT_EFFORT "high"@' -i $run_dir/rm_setup/icc_setup.tcl
sed 's@^set ROUTE_OPT_EFFORT.*@set ROUTE_OPT_EFFORT "high"@' -i $run_dir/rm_setup/icc_setup.tcl
sed 's@^set ICC_TNS_EFFORT_PREROUTE.*@set ICC_TNS_EFFORT_PREROUTE "HIGH"@' -i $run_dir/rm_setup/icc_setup.tcl
sed 's@^set ICC_TNS_EFFORT_POSTROUTE.*@set ICC_TNS_EFFORT_POSTROUTE "HIGH"@' -i $run_dir/rm_setup/icc_setup.tcl

# Some venders need the extra layer IDs.  While this is vendor-specific, I
# don't see a reason to turn it off for everyone else.
sed 's@^set MW_EXTENDED_LAYER_MODE.*@set MW_EXTENDED_LAYER_MODE TRUE@' -i $run_dir/rm_setup/icc_setup.tcl

# For some reason, ICC isn't echoing some of my user input files.  I want it to.
sed 's@source \$@source -echo $@g' -i $run_dir/rm_*/*.tcl

# The only difference between this script and the actual ICC run is that this
# one generates a list of macros that will be used to floorplan the design, while
# the other one actually 
cat > $run_dir/generated-scripts/list_macros.tcl <<EOF
source rm_setup/icc_setup.tcl
open_mw_lib ${top}_LIB
open_mw_cel -readonly init_design_icc

create_floorplan -control_type aspect_ratio -core_aspect_ratio 1 -core_utilization 0.7 -left_io2core 3 -bottom_io2core 3 -right_io2core 3 -top_io2core 3 -start_first_row

set top_left_x [lindex [get_placement_area] 0]
set top_left_y [lindex [get_placement_area] 1]
set bottom_right_x [lindex [get_placement_area] 2]
set bottom_right_y [lindex [get_placement_area] 3]
echo "${top} module=${top} top_left=(\$top_left_x, \$top_left_y) bottom_right=(\$bottom_right_x, \$bottom_right_y)" >> results/${top}.macros.out

set fixed_cells [get_fp_cells -filter "is_fixed == true"]
foreach_in_collection cell \$fixed_cells {
    set full_name [get_attribute \$cell full_name]
    set ref_name [get_attribute \$cell ref_name]
    set height [get_attribute \$cell height]
    set width [get_attribute \$cell width]
    echo "\$full_name parent=${top} module=\$ref_name width=\$width height=\$height" >> results/${top}.macros.out
}
exit
EOF

## FIXME: This throws errors because it's accessing some views on disk.
## I want ICC to try and fix DRCs automatically when possible.  Most of the
## commands are commented out for some reason, this enables them.
#drc_runset="$(echo "${signoff_ruleset[@]}" | xargs basename -s .rs)"
#sed 's@^set ICC_ECO_SIGNOFF_DRC_MODE .*@set ICC_ECO_SIGNOFF_DRC_MODE "AUTO_ECO"@' -i $run_dir/rm_setup/icc_setup.tcl
#sed 's@.*#  s\(.*\)@s\1@' -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl
#sed "s@^\\(signoff_autofix_drc .*\\)@exec $ICV_HOME_DIR/contrib/generate_layer_rule_map.pl -dplog signoff_drc_run/run_details/$drc_runset.dp.log -tech_file $(readlink -f ${tf[@]}) -o signoff_autofix_drc.config\n\\1@" -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl
#sed 's@\$config_file@signoff_autofix_drc.config@' -i $run_dir/rm_icc_zrt_scripts/signoff_drc_icc.tcl

# FIXME: I actually can't insert double vias on SAED32 becaues of DRC errors.
# It smells like the standard cells just aren't setup for it, but this needs to
# be fixed somehow as it'll be necessary for a real chip to come back working.
sed 's@set ICC_DBL_VIA .*@set ICC_DBL_VIA FALSE@' -i $run_dir/rm_setup/icc_setup.tcl
sed 's@set ICC_DBL_VIA_FLOW_EFFORT .*@set ICC_DBL_VIA_FLOW_EFFORT "NONE"@' -i $run_dir/rm_setup/icc_setup.tcl

mkdir -p $run_dir/generated-scripts
if [[ ! -z "$floorplan_json" ]] # if floorplan_json is set
then
    # ICC needs a floorplan in order to do anything.  This script turns the
    # floorplan JSON file into a floorplan TCL file for
    mkdir -p $run_dir/generated-scripts

    cat >$run_dir/saed_32nm.tpl <<EOF
template: m45_mesh(w1, w2) {
  layer : M4 {
     direction : vertical
     width : @w1
     pitch : 8
     spacing : 1
     offset :
  }
  layer : M5 {
     direction : horizontal
     width : @w2
     spacing : 1
     pitch : 8
     offset : 
  }
}
EOF

    python3 $script_dir/floorplan2tcl.py --floorplan_json "$floorplan_json" --output "$run_dir/generated-scripts/floorplan.tcl" --top "$top"
    cat $run_dir/generated-scripts/floorplan.tcl
fi

# Opens the floorplan straight away, which is easier than doing it manually
cat > $run_dir/generated-scripts/open_floorplan.tcl <<EOF
source rm_setup/icc_setup.tcl
open_mw_lib -r ${top}_LIB
open_mw_cel -r floorplan
EOF

cat > $run_dir/generated-scripts/open_floorplan <<EOF
cd $run_dir
source enter
$ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_floorplan.tcl
EOF
chmod +x $run_dir/generated-scripts/open_floorplan

cat > $run_dir/generated-scripts/open_power.tcl <<EOF
source rm_setup/icc_setup.tcl
open_mw_lib -r ${top}_LIB
open_mw_cel -r power
EOF

cat > $run_dir/generated-scripts/open_power <<EOF
cd $run_dir
source enter
$ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_power.tcl
EOF
chmod +x $run_dir/generated-scripts/open_power

cat > $run_dir/generated-scripts/open_chip.tcl <<EOF
source rm_setup/icc_setup.tcl
open_mw_lib -r ${top}_LIB
open_mw_cel -r chip_finish_icc
EOF

cat > $run_dir/generated-scripts/open_chip <<EOF
cd $run_dir
source enter
$ICC_HOME/bin/icc_shell -gui -f generated-scripts/open_chip.tcl
EOF
chmod +x $run_dir/generated-scripts/open_chip

# Write SDF
cat > $run_dir/generated-scripts/write_sdf.tcl <<EOF
source rm_setup/icc_setup.tcl
open_mw_cel \$ICC_OUTPUTS_CEL -lib \$MW_DESIGN_LIBRARY
current_design ${top}
write_sdf \$RESULTS_DIR/\$DESIGN_NAME.output.sdf
exit
EOF

cat > $run_dir/generated-scripts/write_sdf <<EOF
cd $run_dir
$ICC_HOME/bin/icc_shell -f generated-scripts/write_sdf.tcl
EOF
chmod +x $run_dir/generated-scripts/write_sdf
