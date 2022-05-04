.. _tech-json:

Hammer Tech JSON
===============================

The ``tech.json`` for a given technology sets up some general information about the install of the PDK, sets up DRC rule decks, sets up pointers to PDK files, and supplies technology stackup information. For a full schema that the tech JSON supports, please see ``src/hammer-tech/schema.json``.

Technology Install
---------------------------------

The user may supply the PDK to Hammer as an already extracted directory and/or as a tarball that Hammer can automatically extract. Setting ``technology.TECH_NAME.`` ``install_dir`` and/or ``tarball_dir`` (key is setup in the defaults.yml) will fill in as the path prefix for paths supplied to PDK files in the rest of the ``tech.json``. :numref:`install-example` shows an example of the installs and tarballs from the ASAP7 plugin.

.. _install-example:
.. code-block:: json

  "name": "ASAP7 Library",
  "grid_unit": "0.001",
  "time_unit": "1 ps",
  "installs": [
    {
      "path": "$PDK",
      "base var": "technology.asap7.pdk_install_dir"
    },
    {
      "path": "$STDCELLS",
      "base var": "technology.asap7.stdcell_install_dir"
    },
    {
      "path": "tech-asap7-cache",
      "base var": ""
    }
  ],
  "tarballs": [
    {
      "path": "ASAP7_PDK_CalibreDeck.tar",
      "homepage": "http://asap.asu.edu/asap/",
      "base var": "technology.asap7.tarball_dir"
    }
  ],

Notice how in the installs, there are two directories holding the PDK files and standard cell files. The ``tech-asap7-cache`` with an empty ``base var`` denotes files that exist in the tech cache, which are placed there by a post-installation PDK hacking script (see ASAP7's ``post_install_script`` method). Finally, the encrypted Calibre decks are provided in a tarball.

DRC/LVS Deck Setup
---------------------------------

As many DRC & LVS decks for as many tools can be specified in the ``drc decks`` and ``lvs decks`` keys. Additional DRC/LVS commands can be appended to the generated run files by specifying raw text in the ``additional_drc_text`` and ``additional_lvs_text`` keys. :numref:`deck-example` shows an example of an LVS deck from the ASAP7 plugin.

.. _deck-example:
.. code-block:: json

  "lvs decks": [
    {
      "tool name": "calibre",
      "deck name": "all_lvs",
      "path": "ASAP7_PDK_CalibreDeck.tar/calibredecks_r1p7/calibre/ruledirs/lvs/lvsRules_calibre_asap7.rul"
    }
  ],
  "additional_lvs_text": "LVS SPICE EXCLUDE CELL \*SRAM*RW*\"\nLVS BOX \"SRAM*RW*\"\nLVS FILTER \*SRAM*RW*\" OPEN", 

The file pointers, in this case, use the tarball prefix because Hammer will be extracting the rule deck directly from the ASAP7 tarball. The additional text is needed to tell Calibre that the dummy SRAM cells need to be filtered from the source netlist and boxed and filtered from the layout.

Library Setup
---------------------------------

The ``libraries`` key also must be setup in the JSON plugin. This will tell Hammer where to find all of the relevant files for standard cells and other blocks for the VLSI flow. :numref:`library-example` shows an example of the start of the library setup and one entry from the ASAP7 plugin.


.. _library-example:
.. code-block:: json

  "libraries": [
    {
      "lef file": "$STDCELLS/techlef_misc/asap7_tech_4x_201209.lef",
      "provides": [
        {
          "lib_type": "technology"
        }
      ]
    },
    {
      "nldm liberty file": "$STDCELLS/LIB/NLDM/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib.gz",
      "verilog sim": "$STDCELLS/Verilog/asap7sc7p5t_SIMPLE_RVT_TT_201020.v",
      "lef file": "$STDCELLS/LEF/scaled/asap7sc7p5t_27_R_4x_201211.lef",
      "spice file": "$STDCELLS/CDL/LVS/asap7sc7p5t_27_R.cdl",
      "gds file": "$STDCELLS/GDS/asap7sc7p5t_27_R_201211.gds",
      "qrc techfile": "$STDCELLS/qrc/qrcTechFile_typ03_scaled4xV06",
      "spice model file": {
        "path": "$PDK/models/hspice/7nm_TT.pm"
      },
      "corner": {
        "nmos": "typical",
        "pmos": "typical",
        "temperature": "25 C"
      },
      "supplies": {
        "VDD": "0.70 V",
        "GND": "0 V"
      },
      "provides": [
        {
          "lib_type": "stdcell",
          "vt": "RVT"
        }
      ]
    },

The file pointers, in this case, use the ``$PDK`` and ``$STDCELLS`` prefix as defined in the installs.  The ``corner`` key tells Hammer what process and temperature corner that these files correspond to.  The ``supplies`` key tells Hammer what the nominal supply for these cells are.  
The ``provides`` key has several sub-keys that tell Hammer what kind of library this is (examples include ``stdcell``, ``fiducials``, ``io pad cells``, ``bump``, and ``level shifters``) and the threshold voltage flavor of the cells, if applicable.
Adding the tech LEF for the technology with the ``lib_type`` set as ``technology`` is necessary for place and route.

..
TODO: ADD INFO ABOUT LIBRARY FILTERS

Stackup
--------------------------------
The ``stackups`` sets up the important metal layer information for Hammer to use. :numref:`stackups-example` shows an example of one metal layer in the ``metals`` list from the ASAP7 example tech plugin.   

.. _stackups-example:
.. code-block:: json

        {"name": "M3", "index": 3, "direction": "vertical", "min_width": 0.072, "pitch": 0.144, "offset": 0.0, "power_strap_widths_and_spacings": [{"width_at_least": 0.0, "min_spacing": 0.072}], "power_strap_width_table": [0.072, 0.36, 0.648, 0.936, 1.224, 1.512]}

All this information is typically taken from the tech LEF and can be automatically filled in with a script. The metal layer name and layer number is specified. ``direction`` specifies the preferred routing direction for the layer. ``min_width`` and ``pitch`` specify the minimum width wire and the track pitch, respectively.  ``power_strap_widths_and_spacings`` is a list of pairs that specify design rules relating to the widths of wires and minimum required spacing between them. This information is used by Hammer when drawing power straps to make sure it is conforming to some basic design rules. 

        
Sites
--------------------------------
The ``sites`` field specifies the unit standard cell size of the technology for Hammer.

.. _sites-example:
.. code-block:: json

  "sites": [
    {"name": "asap7sc7p5t", "x": 0.216, "y": 1.08}
  ]

This is an example from the ASAP7 tech plugin in which the ``name`` parameter specifies the core site name used in the tech LEF, and the ``x`` and ``y`` parameters specify the width and height of the unit standard cell size, respectively.

Special Cells
--------------------------------
The ``special cells`` field specifies a set of cells in the technology that have special functions. :numref:`special-cells-example` shows a subset of the ASAP7 tech plugin for 2 types of cells: ``tapcell`` and ``stdfiller``.

.. _special-cells-example:
.. code-block:: json

  "special cells": [
    {"cell_type": "tapcell", "name": ["TAPCELL_ASAP7_75t_L"]},
    {"cell_type": "stdfiller", "name": ["FILLER_ASAP7_75t_R", "FILLER_ASAP7_75t_L", "FILLER_ASAP7_75t_SL", "FILLER_ASAP7_75t_SRAM", "FILLERxp5_ASAP7_75t_R", "FILLERxp5_ASAP7_75t_L", "FILLERxp5_ASAP7_75t_SL", "FILLERxp5_ASAP7_75t_SRAM"]},

There are 8 ``cell_type`` s supported: ``tiehicell``, ``tielocell``, ``tiehilocell``, ``endcap``, ``iofiller``, ``stdfiller``, ``decap``, and ``tapcell``. Depending on the tech/tool, some of these cell types can only have 1 cell in the ``name`` list.

There is an optional ``size`` list. For each element in its corresponding ``name`` list, a size (type: str) can be given. An example of how this is used is for ``decap`` cells, where each listed cell has a typical capacitance, which a place and route tool can then use to place decaps to hit a target total decapacitance value. After characterizing the ASAP7 decaps using Voltus, the nominal capacitance is filled into the ``size`` list:

.. code-block:: json

    {"cell_type": "decap", "name": ["DECAPx1_ASAP7_75t_R", "DECAPx1_ASAP7_75t_L", "DECAPx1_ASAP7_75t_SL", "DECAPx1_ASAP7_75t_SRAM", "DECAPx2_ASAP7_75t_R", "DECAPx2_ASAP7_75t_L", "DECAPx2_ASAP7_75t_SL", "DECAPx2_ASAP7_75t_SRAM", "DECAPx2b_ASAP7_75t_R", "DECAPx2b_ASAP7_75t_L", "DECAPx2b_ASAP7_75t_SL", "DECAPx2b_ASAP7_75t_SRAM", "DECAPx4_ASAP7_75t_R", "DECAPx4_ASAP7_75t_L", "DECAPx4_ASAP7_75t_SL", "DECAPx4_ASAP7_75t_SRAM", "DECAPx6_ASAP7_75t_R", "DECAPx6_ASAP7_75t_L", "DECAPx6_ASAP7_75t_SL", "DECAPx6_ASAP7_75t_SRAM", "DECAPx10_ASAP7_75t_R", "DECAPx10_ASAP7_75t_L", "DECAPx10_ASAP7_75t_SL", "DECAPx10_ASAP7_75t_SRAM"], "size": ["0.39637 fF", "0.402151 fF", "0.406615 fF", "0.377040 fF","0.792751 fF", "0.804301 fF", "0.813231 fF", "0.74080 fF", "0.792761 fF", "0.804309 fF", "0.813238 fF","0.75409 fF", "1.5855 fF", "1.6086 fF", "1.62646 fF", "1.50861 fF", "2.37825 fF", "2.4129 fF", "2.43969 fF", "2.26224 fF", "3.96376 fF", "4.02151 fF", "4.06615 fF", "3.7704 fF"]},

Don't Use, Physical-Only Cells
--------------------------------
The ``dont use list`` is used to denote cells that should be excluded due to things like bad timing models or layout.
The ``physical only cells list`` is used to denote cells that contain only physical geometry, which means that they should be excluded from netlisting for simulation and LVS. Examples from the ASAP7 plugin are below:

.. code-block:: json

  "dont use list": [
      "ICGx*DC*",
      "AND4x1*",
      "SDFLx2*",
      "AO21x1*",
      "XOR2x2*",
      "OAI31xp33*",
      "OAI221xp5*",
      "SDFLx3*",
      "SDFLx1*",
      "AOI211xp5*",
      "OAI322xp33*",
      "OR2x6*",
      "A2O1A1O1Ixp25*",
      "XNOR2x1*",
      "OAI32xp33*",
      "FAx1*",
      "OAI21x1*",
      "OAI31xp67*",
      "OAI33xp33*",
      "AO21x2*",
      "AOI32xp33*"
  ],
  "physical only cells list": [
    "TAPCELL_ASAP7_75t_R", "TAPCELL_ASAP7_75t_L", "TAPCELL_ASAP7_75t_SL", "TAPCELL_ASAP7_75t_SRAM",
    "TAPCELL_WITH_FILLER_ASAP7_75t_R", "TAPCELL_WITH_FILLER_ASAP7_75t_L", "TAPCELL_WITH_FILLER_ASAP7_75t_SL", "TAPCELL_WITH_FILLER_ASAP7_75t_SRAM",
    "FILLER_ASAP7_75t_R", "FILLER_ASAP7_75t_L", "FILLER_ASAP7_75t_SL", "FILLER_ASAP7_75t_SRAM", 
    "FILLERxp5_ASAP7_75t_R", "FILLERxp5_ASAP7_75t_L", "FILLERxp5_ASAP7_75t_SL", "FILLERxp5_ASAP7_75t_SRAM"
  ],
