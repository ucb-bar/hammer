############################################################
#
# find_force_registers.tcl:
#
# This procedure finds all the registers in your design and
# writes VCS "force -deposit" commands to set them to a known
# state at simulation time 0.
#
# This is useful if your design contains non reset registers
# which are intialised to "x" and cause x
# propagation in your simulation.
#
# Use this script in DC or ICC, then read the output into VCS.
#
#  NOTE!!!  YOU ARE MUST CHECK THAT ANY REGISTERS WHICH ARE
#           NOT RESET IN YOUR DESIGN DO NOT CAUSE FUNCTIONAL
#	    PROBLEMS!  This script could well mask such
#	    functional problems.  Check your design initialises
#	    correctly.
#
# Use:
#	1) Read design and link
#	2) Source this file
#	3) find_force_registers "Testbench prefix"
#			 <force script>
#			<force to value (0 or 1)>
#			<PLI table file>
#
# "Testbench prefix" is the VCS pathname of your netlist.  For
# instance, if your design is instanced in your testbench as
# tb.dut, specify tb.dut to this argument.
#
# <force script> is the name of the script containing the force
# statements.  Read this at time 0 on the VCS ucli command line.
# Default: force_regs.tcl
#
# <force to value> should be 0 or 1 - the value you want to force
# all registers to be.
# Default: 0
#
# <PLI table file> is the name of the PLI table file that VCS will
# read.  VCS needs special access to the registers you'll be
# forcing - this file does this.  Read this into VCS with the -P
# option
# Default: access.tab
#
##############################################################

proc find_regs { 				 \
			tb_prefix 			 \
			{force_val 0} 			 \
			{force_script "force_regs.ucli"} \
			{pli_tab_file "access.tab"}}     {

  set regs ""
  set refs ""
  foreach_in_collection reg [all_registers]  {
    # Keep a list of all the library cell names in the design
    if { [lsearch $refs [get_attribute $reg ref_name]] == -1 } {
      lappend refs [get_attribute $reg ref_name]
    }
    # Keep a list of all the register pathnames in the design
    foreach pins [get_object_name [filter [get_pins -of_object $reg] {@pin_direction == out}]] {
      lappend regs $pins
    }
  }
  redirect $force_script {echo ""}
  foreach myreg $regs {
    # DC/ICC hierarchical separator is "/", but VCS needs "."
    regsub -all {/}  $myreg . thisreg
    # Some pins might have "[" or "]", which will confuse ucli
    regsub -all {\[} $thisreg \\\[ this_reg
    regsub -all {\]} $this_reg \\\] thisreg
    redirect -append $force_script {echo "force -deposit ${tb_prefix}.${thisreg} $force_val"}
  }

  redirect $pli_tab_file {echo ""}
  foreach myref $refs {
    redirect -append $pli_tab_file {echo "acc+=wn:$myref"}
  }

}
