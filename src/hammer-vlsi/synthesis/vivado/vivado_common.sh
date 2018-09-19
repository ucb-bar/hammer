#!/bin/bash
# Common parameters for Vivado invocation.
# Parses the command-line options passed to the including script.


script_dir="$(dirname "$0")"

unset vivado
v=()
unset dcp
unset dcp_macro_dir
unset output
unset board_files
unset top
unset sram_module
unset width
unset depth
lib=()
while [[ "$1" != "" ]]
do
    case "$1" in
    "$0") ;;
    */vivado) vivado="$1";;
    *.v) v+=("$1");;
    "-o") output="$2"; shift;;
    "--dcp") dcp="$2"; shift;;
    "--dcp_macro_dir") dcp_macro_dir="$2"; shift;;
    "--board_files") board_files="$2"; shift;;
    "--top") top="$2"; shift;;
    "--sram-module") sram_module="$2"; shift;;
    "--width") width="$2"; shift;;
    "--depth") depth="$2"; shift;;
    *.lib) lib+=("$1");;
    *.dcp) ;; # TODO: remove this hack. Need to swallow .dcp or figure out a better way to pass all the verilog files
    *) echo "Unknown argument $1"; exit 1;;
    esac
    shift
done


VIVADOFLAGS="-nojournal -mode batch -source board.tcl -source paths.tcl -source project.tcl\
 -source prologue.tcl -source init.tcl -source syn.tcl"
