Sky130 Technology Library
=========================
Hammer now supports the Skywater 130nm Technology process. The [SkyWater Open Source PDK](https://skywater-pdk.readthedocs.io/) is a collaboration between Google and SkyWater Technology Foundry to provide a fully open source Process Design Kit (PDK) and related resources, which can be used to create manufacturable designs at SkyWater’s facility.
The Skywater 130nm PDK files are located in a repo called [skywater-pdk](https://github.com/google/skywater-pdk/) A tool called [Open-PDKs (open_pdks)](https://github.com/RTimothyEdwards/open_pdks/) was developed to generate all the files typically found in a PDK.
Open-PDKs uses the contents in `skywater-pdk`, and outputs files to a directory called `sky130A`.

[OpenLANE](https://github.com/efabless/openlane/) is an open-source RTL to GDSII VLSI flow that supports Sky130.


Before setting up the Sky130 PDK, we recommend familiarizing yourself with the process's documentation [summarized below](#Resources).

PDK Structure
-------------

OpenLANE expects a certain file structure for the Sky130 PDK. 
We recommend adhering to this file structure for Hammer as well.
All the files reside in a root folder (named something like `skywater` or `sky130`).
The environment variable `$PDK_ROOT` should be set to this folder's path:

    export PDK_ROOT=<path-to-skywater-directory>
    
`$PDK_ROOT` contains the following:

* `skywater-pdk`

  * Original PDK source files

* `open_pdks`

  * install of Open-PDKs tool

* `share/pdk/sky130A`

  * output files from Open-PDKs compilation process

NDA Files
---------
Using commercial VLSI tools with this process requires files that are currently under NDA. 
If you have access to these, you will be able to use the Hammer VLSI flow out-of-the-box with the Sky130 process.
Some of these NDA files, such as the Calibre DRC/LVS decks, rely on the environment variable `$PDK_HOME` containing the path to the version of the NDA files you are using.
You may set it in the Hammer plugin, or as follows:

    export PDK_HOME=<path-to-skywater-src-nda>/s8/<version#>

This plugin has been tested with PDK version `V2.0.1`; your mileage may vary for other versions.

Prerequisites for PDK Setup
---------------------------

* [Magic](http://opencircuitdesign.com/magic/)

  * required for `open_pdks` file generation
  * tricky to install, closely follow the directions on the `Install` page of the website
  
    * as the directions indicate, you will likely need to manually specify the location of the Tcl/Tk package installation using `--with-tcl` and `--with-tk`
 
 If using conda, these installs alone caused the Magic install to work:

    conda install -c intel tcl 
    conda install -c anaconda tk 
    conda install -c anaconda libglu

OpenRAM SRAMs
-------------
TODO: add overview here

    git clone https://github.com/efabless/sky130_sram_macros.git
    

PDK Setup
---------
In `$PDK_ROOT`, clone the skywater-pdk repo and generate the liberty files for each library:

    git clone https://github.com/google/skywater-pdk.git
    cd skywater-pdk
    # Expect a large download! ~7GB at time of writing.
    git submodule init libraries/*/latest
    git submodule update
    # Regenerate liberty files
    make timing

Again in `$PDK_ROOT`, clone the open_pdks repo and run the install process to generate the `sky130A` directory:

    git clone https://github.com/RTimothyEdwards/open_pdks.git
    cd open_pdks
    ./configure \
    --enable-sky130-pdk=$PDK_ROOT/skywater-pdk/libraries \
    --prefix=$PDK_ROOT \
    --enable-sram-sky130=$PDK_ROOT/sky130_sram_macros # if using SRAMs
    make
    make install

This generates all the Sky130 PDK files and installs them to `$PDK_ROOT/share/pdk/sky130A`

Known DRC Issues
----------------
The Hammer flow generates DRC-clean digital logic when run with the Calibre DRC deck and SRAMs excluded. 

TODO: summarize issues with SRAMs and open-source Magic DRC checks.

## Resources
The good thing about this process being open-source is that most questions about the process are answerable through a google search. 
The tradeoff is that the documentation is a bit of a mess, and is currently scattered over a few pages and Github repos. 
We try to summarize these below.

Git repos:

* [SkyWater Open Source PDK](https://github.com/google/skywater-pdk/)

  * Git repo of the main Skywater 130nm files

* [Open-PDKs](https://github.com/RTimothyEdwards/open_pdks/)

  * Git repo of Open-PDKs tool that compiles the Sky130 PDK

* [Git repos on foss-eda-tools](https://foss-eda-tools.googlesource.com/)

  * Additional useful repos, such as Berkeley Analog Generator (BAG) setup

Documentation:

* [SkyWater SKY130 PDK's documentation](https://skywater-pdk.readthedocs.io)

  * Main documentation site for the PDK

* [Join the SkyWater PDK Slack Channel](https://join.skywater.tools/)

  * By far the best way to have questions about the process answered, with 80+ channels for different topics

* [Skywater130 Standard Cell and Primitives Overview](http://diychip.org/sky130/)

  * Additional useful documentation for the PDK

* [FOSSi Foundation YouTube Channel](https://www.youtube.com/c/FOSSiFoundation/)

  * Contains informational videos on the Sky130 process, OpenLANE flow, and Efabless Shuttle program

SRAMs:

* [OpenRAM](https://github.com/VLSIDA/OpenRAM/)

  * Open-source static random access memory (SRAM) compiler

* [OpenRAM pre-compiled macros](https://github.com/efabless/sky130_sram_macros/)

  * Precompiled sizes are 1kbytes, 2kbytes and 4kbytes

OpenLANE flow:

* [OpenLANE](https://github.com/efabless/openlane/)

  * Open-source RTL to GDSII flow
  
* [Magic](http://opencircuitdesign.com/magic/)

  * Open-source VLSI layout tool that handles DRC checks in OpenLANE
  
