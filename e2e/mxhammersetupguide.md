# Provisional MXHammer Setup Guide (E2E)

## 1. Hammer Setup
### 1.1 Setup the Hammer environment according to the steps under 1.2.2. Developer Setup in the Hammer documentation, found [here](https://hammer-vlsi.readthedocs.io/en/stable/Hammer-Basics/Hammer-Setup.html#developer-setup) or below.

#### 1.2.2. Developer Setup
##### 1. Clone Hammer with `git`
```
git clone https://github.com/ucb-bar/hammer.git
cd hammer
```
##### 2. [Install poetry](https://python-poetry.org/docs/master/) to manage the development virtualenv and dependencies
```
curl -sSL https://install.python-poetry.org | python3 -
```
##### 3. Create a poetry-managed virtualenv using the dependencies from `pyproject.toml`
```
# create the virtualenv inside the project folder (in .venv)
poetry config virtualenvs.in-project true
poetry install
```
##### 4. Activate the virtualenv. Within the virtualenv, Hammer is installed and you can access its scripts defined in `pyproject.toml` (in `[tool.poetry.scripts]`)
```
poetry shell
hammer-vlsi -h
```
### 1.2 Set simulator to Xcelium
Under `hammer/e2e/configs-tool/cm.yml`, find the simulator tool key: `vlsi.core.sim_tool` and change the value from VCS to Xcelium. This should like the following when done: `vlsi.core.sim_tool: "hammer.sim.xcelium"`.

### 1.3 Setup design configuration file
Create a folder under `hammer/e2e/configs-design` to hold the configuration files for your design. For the AMS simulation, at minimum, this folder should contain a `common.yml`, `sim-rtl.yml`, and a process configuration file such as `asap7.yml` or `sky130.yml`. 


## 2. MXHammer Setup

### 2.1 Replace standard Xcelium plugin files with their MXHammer variants
The files for the MXHammer variant of Hammer can be found in the `ams_experimental` branch of [Hammer](https://github.com/ucb-bar/hammer.git). If you have the correct files, the following comment should appear within the `__init__.py`: `# MXHammer version` .

### 2.2 Simulator Setup
#### 2.2.1 General Simulator Settings
The first portion of your `sim-rtl.yml` should contain general simulator settings, such as the top module, testbench name/DUT, etc. **The level setting should be set to "rtl".** It should look something like the following when filled:
```
sim.inputs:
	top_module: "modulename"
	tb_name: "testbench"
	tb_dut: "module0"
	level: "rtl"
	input_files: ["src/digital/inv.v", "src/digital/testbench.vams"]
	timescale: "1ns/100ps"
	waveform.type: null
	waveform.dump_name: "wave"
	waveform.compression: False
	waveform.probe_paths: "-all"
	waveform.tcl_opts: null
```
All Verilog/VHDL and Verilog-AMS files should be included within `input_files`, except for connect module library files, and AMS connection rule files. These are explained later below.

#### 2.2.2 Xcelium Simulator Settings
The second portion of your `sim-rtl.yml` should contain Xcelium-specific settings for digital and optionally AMS simulation. In order to see what each key expects as a value, please see `defaults.yml` within `hammer/hammer/sim/xcelium`. 

However, particular elements may be unfamiliar, such as `disciplines`, `connectlibs`, and `connrules`. 

##### Disciplines
These are a set of definitions and properties for a specific type of system. It is a combination of an analog **potential** (ex. voltage) and ***flow* nature** (ex. current). **Natures** are declarations that define a collection of **attributes**. The defined nature is then used to define disciplines and other natures.

##### Disciplines for specific scopes
We can use `-setdiscipline` or `-setd` option to specify to the elaborator which disciplines to apply to domain-less (think voltage for analog, or high/low for digital) nets in a specified design scope. 

The following is the syntax for specifying disciplines:
```
-setd "LIB-lib_name- discipline_name"
-setd "CELL-lib_name.cell_name:view_name- discipline_name"
-setd "CELLTERM-cell_name.port_name- discipline_name"
-setd "INST-hierarchical_instance_name- discipline_name"
-setd "INSTTERM-hierarchical_instance_name- discipline_name"
```
Example disciplines for a 3.3V Buffer:
```
-SETD "INSTTERM-testbench.vlog_buf.I1.in- logic33V"
-SETD "INSTTERM-testbench.vlog_buf.in_33v- logic33V"
-SETD "INSTTERM-testbench.vlog_buf.out_33v- logic33V"
-SETD "INSTTERM-testbench.vlog_buf.I2.out- logic33V"
```

`-setdisciple` \ `-setd` can also be used to allow default default disciplines to be applied to different blocks.
```
-discipline logic 18V
	-setd "inst-top.I1.I2- logic_33V"
	-setd "inst-top.I1.I3- logic_5V"
	-setd "inst-top.I1.I4- electrical"
	-setd "net-top.I1.out- logic_33V"
```
##### Discipline specification for MXHammer
Place all disciplines, formatted in the manner shown above, within a .txt file and provide the path to the file relative to the working directory to the `sim.xcelium.disciplines` key. 

##### Connect Modules (CMs) / Interface Elements (IEs)
Connect modules or interface elements slot between signal domains like electrical, logic, and real. They are inserted *automatically* or *manually* by using connect or **ie** statements, which contain the code required to translate and propagate signals between **nets** that have different **disciplines** connected through a port.

##### Connect Libraries
The connect libraries are a set of files which define how signal domains should be translated between various **disciplines**. As of now they are not included within the public-facing version of MXHammer.

##### Connect Rules
Defines a set of **connect modules** to be used in a design and notifies the simulator about which CMs to use and which is chosen from the built-in set provided in the software installation or from a user-defined set

### 2.3 A/MS Control Files
For an AMS simulation, we need to specify the analog signals, models used in the design, which analog simulation we wish to perform, the analog design itself, and how we want to connect that design to external blocks through and **AMSD** block.

#### 2.3.1 AMSD Control Files
The AMS control file (**AMSCF**) specifies:
 - The simulator language (should be spectre in most cases)
 - Global signals (such as `0`/`vss!` and `vdd!`)
 - The models to be used in the simulation of the design, an **analog control file** (if the information within the **ACF** is not included within an **AMSD** block within the **AMSCF**). ***ALL*** model files used within the design **must** be included (section of the model the particular block resides in is usually fine).
		 - **NOTE:** When generating the netlist for your analog design, do so as **CDL**. This can be done from **ICADV** GUI as File -> Export -> CDL. Alternatively you can use the Virtuoso CDL out interface.
 - The design(s), whose file(s) must be included, like the model files.
 - **AMSD** Block(s)

##### AMSD Blocks
These 'AMS Designer' blocks can contain any design partitioning, disciplines, and connect modules. Where 'partitioning' includes setting the use of spice, portmaps for subcircuits, bus delimiters, and setting `autobus` to `yes` or `no`. Disciplines include connecting the power supply voltage when connecting from an analog voltage to logic.

Ex 1: `ie vsup=1.8 discipline=logic18V` tells the elaborator that 1.8V is a logic 1 for that the analog real output

Ex 2: A generic, mostly unfilled AMSD block might look like the following:
```
amsd{

// set the connect rule power supply
   ie vsup=? discipline=logic?V

// mix analog and digital
portmap subckt=ckt_name autobus=yes busdelim="[] <>" 
config cell=ckt_name use=spice
}
```

##### AMSCF Example for a skywater 130nm level-shifter
In the following example, notice `autobus` is set to `yes`, this specifies that Xcelium will automatically generate CMs/IEs between nets with different domains.
```
simulator lang=spectre 

// global signals
global 0 vdd!

//model deck - Skywater
include "/tools/C/miguel4141/mxhammer/mx-project/bag-sky130/bag3_skywater130_workspace/skywater130/workspace_setup/PDK/MODELS/SPECTRE/s8phirs_10r/Models/design_wrapper.lib.scs" section=tt_fet
include "/tools/C/miguel4141/mxhammer/mx-project/bag-sky130/bag3_skywater130_workspace/skywater130/workspace_setup/PDK/MODELS/SPECTRE/s8phirs_10r/Models/design_wrapper.lib.scs" section=tt_cell
include "/tools/C/miguel4141/mxhammer/mx-project/bag-sky130/bag3_skywater130_workspace/skywater130/workspace_setup/PDK/MODELS/SPECTRE/s8phirs_10r/Models/design_wrapper.lib.scs" section=tt_parRC
include "/tools/C/miguel4141/mxhammer/mx-project/bag-sky130/bag3_skywater130_workspace/skywater130/workspace_setup/PDK/MODELS/SPECTRE/s8phirs_10r/Models/design_wrapper.lib.scs" section=tt_rc
include "/tools/C/miguel4141/mxhammer/mx-project/bag-sky130/bag3_skywater130_workspace/skywater130/workspace_setup/PDK/MODELS/SPECTRE/s8phirs_10r/Models/design_wrapper.lib.scs" section=npn_t

//Analog Control File
include "acf.scs"

//Cadence Level Shifter
//include "src/analog/level_shifter.sp"

//Skywater Level Shifter
include "src/analog/sky130_level_shifter.sp"

// ams configuration options
amsd{

// set the connect rule power supply
   ie vsup=1.8 discipline=logic18V

// mix analog and digital
portmap subckt=sky130_level_shifter autobus=yes busdelim="[] <>" 
config cell=sky130_level_shifter use=spice
}

```

#### 2.3.2 Analog Control Files
The analog control file (**ACF**) contains the analog simulation type and settings which the AMS simulation will use. They are specified in the spectre language.

Ex:
```
***********************************
simulator lang=spectre
***********************************

*--------------------------------------------------------*
* Spectre Fast APS Analysis Options/Spectre X options
*--------------------------------------------------------*
tran1 tran start=1ns stop=1us method=trap
                                                                                
*--------------------------------------------------------*
* Spectre Fast APS Simulator Options options
*--------------------------------------------------------*
save * sigtype=node depth=4         
```

## 2.4 Running MXHammer
To run the AMS simulation, ensure that the `ams` key in `sim-rtl.yml` is set to `True` and you have all other relevant files and values to the keys set. For any keys whose value is a path to a file or directory which is not needed for your simulation (such as `connectlibs` or `connectrules`), set that value to `None` in `sim-rtl.yml`. Additionally, some additional options are currently hardcoded, so please be sure to use a `.tcl` file to specify which signals you would like to save from the AMS simulation, name that file `probe.tcl`, and put it in `e2e/src/`. If you are unfamiliar with how to put together a `.tcl` probe, a guide can be found [here](https://community.cadence.com/cadence_blogs_8/b/cic/posts/start-your-engines-use-tcl-commands-to-save-signals-more-efficiently-in-mixed-signal-simulations).

### 2.4.1 Xcelium + MXHammer Mechanics
Xcelium works in one of two primary methodologies, **three-step** or **single-step**. In the three-step methodology, the user (or Hammer) steps through the compilation, elaboration, and simulation stages. In the single-step methodology, the user provides all necessary information up front and Xcelium internally steps through all three stages. The base Xcelium plugin operates off of the three-step methodology.

MXHammer operates on a pseudo-three-step methodology which takes in the arguments generated by the three-step process of the base digital-only Xcelium plugin and the specified AMS arguments to create a shell script for a single run.

### 2.4.2 Starting the MXHammer run
To begin the MXHammer, simply go to your hammer folder, initiate the poetry environment, then go to the `e2e` folder. Once there, type `make build` into the command line to generate the `hammer.d` file and then type `make sim-rtl` to begin the run.


### 2.4.3 Initiating the AMS Simulation
Currently, there are issues with the step of initiating the run automatically, so you will likely need to do so yourself. All you need to do so is to go to the build directory under `e2e`, under which you fill find the build for your design, under which you can find `sim-rtl-rundir` (the full path will look something like `hammer/e2e/build-node-env/design_name/sim-rtl-rundir`). Once you are there, ensure the `run_mxh` shell script has the correct permissions and then simply type `./run_mxh` into the command line.


# For any questions, email Miguel at miguel4141@berkeley.edu
