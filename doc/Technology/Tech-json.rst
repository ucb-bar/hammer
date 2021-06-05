.. _tech-json:

Hammer Tech JSON
===============================

The ``tech.json`` for a given technology sets up some general information about the install of the PDK, sets up DRC rule decks, sets up pointers to PDK files, and supplies technology stackup information. 

Technology Install
---------------------------------

The user may supply the PDK to Hammer either as an already extracted directory or as a tarball that Hammer can automatically extract. Setting ``technology.TECH_NAME.`` ``install_dir`` or ``tarball_dir`` (key is setup in the defaults.yml) will fill in as the path prefix for paths supplied to PDK files in the rest of the ``tech.json``.

DRC/LVS Deck Setup
---------------------------------

As many DRC & LVS decks for as many tools can be specified in the ``drc decks`` and ``lvs decks`` keys. Additional DRC/LVS commands can be appended to the generated run files by specifying raw text in the ``additional_drc_text`` and ``additional_lvs_text`` keys. :numref:`deck-example` shows an example of an LVS deck from the ASAP7 plugin.

.. _deck-example:
.. code-block:: json

  "lvs decks": [
    {
      "tool name": "calibre",
      "deck name": "all_lvs",
      "path": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs/lvs/lvsRules_calibre_asap7.rul"
    }
  ],
  "additional_lvs_text": "LVS BOX DECAPx1_ASAP7_75t_R\nLVS BOX DECAPx1_ASAP7_75t_L\nLVS BOX DECAPx1_ASAP7_75t_SL\nLVS BOX DECAPx1_ASAP7_75t_SRAM\nLVS BOX DECAPx2_ASAP7_75t_R\nLVS BOX DECAPx2_ASAP7_75t_L\nLVS BOX DECAPx2_ASAP7_75t_SL\nLVS BOX DECAPx2_ASAP7_75t_SRAM\nLVS BOX DECAPx4_ASAP7_75t_R\nLVS BOX DECAPx4_ASAP7_75t_L\nLVS BOX DECAPx4_ASAP7_75t_SL\nLVS BOX DECAPx4_ASAP7_75t_SRAM\nLVS BOX DECAPx6_ASAP7_75t_R\nLVS BOX DECAPx6_ASAP7_75t_L\nLVS BOX DECAPx6_ASAP7_75t_SL\nLVS BOX DECAPx6_ASAP7_75t_SRAM\nLVS BOX DECAPx10_ASAP7_75t_R\nLVS BOX DECAPx10_ASAP7_75t_L\nLVS BOX DECAPx10_ASAP7_75t_SL\nLVS BOX DECAPx10_ASAP7_75t_SRAM\nLVS FILTER DECAPx1_ASAP7_75t_R OPEN\nLVS FILTER DECAPx1_ASAP7_75t_L OPEN\nLVS FILTER DECAPx1_ASAP7_75t_SL OPEN\nLVS FILTER DECAPx1_ASAP7_75t_SRAM OPEN\nLVS FILTER DECAPx2_ASAP7_75t_R OPEN\nLVS FILTER DECAPx2_ASAP7_75t_L OPEN\nLVS FILTER DECAPx2_ASAP7_75t_SL OPEN\nLVS FILTER DECAPx2_ASAP7_75t_SRAM OPEN\nLVS FILTER DECAPx4_ASAP7_75t_R OPEN\nLVS FILTER DECAPx4_ASAP7_75t_L OPEN\nLVS FILTER DECAPx4_ASAP7_75t_SL OPEN\nLVS FILTER DECAPx4_ASAP7_75t_SRAM OPEN\nLVS FILTER DECAPx6_ASAP7_75t_R OPEN\nLVS FILTER DECAPx6_ASAP7_75t_L OPEN\nLVS FILTER DECAPx6_ASAP7_75t_SL OPEN\nLVS FILTER DECAPx6_ASAP7_75t_SRAM OPEN\nLVS FILTER DECAPx10_ASAP7_75t_R OPEN\nLVS FILTER DECAPx10_ASAP7_75t_L OPEN\nLVS FILTER DECAPx10_ASAP7_75t_SL OPEN\nLVS FILTER DECAPx10_ASAP7_75t_SRAM OPEN", 

The file pointers, in this case, use the tarball prefix because Hammer will be extracting the rule deck directly from the ASAP7 tarball. The additional text is needed to tell Calibre that the decap cells need to be filtered from the source netlists.

Library Setup
---------------------------------

The ``libraries`` key also must be setup in the JSON plugin. This will tell Hammer where to find all of the relevant files for standard cells and other blocks for the VLSI flow. :numref:`library-example` shows an example of the start of the library setup and one entry from the ASAP7 plugin.


.. _library-example:
.. code-block:: json

  "libraries": [
    {
      "lef file": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/techlef_misc/asap7_tech_4x_170803.lef",
      "provides": [
        {
          "lib_type": "technology"
        }
      ]
    },
    {
      "nldm liberty file": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/lib/asap7sc7p5t_24_SIMPLE_RVT_TT.lib",
      "verilog sim": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/verilog/asap7sc7p5t_24_SIMPLE_RVT_TT.v",
      "lef file": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/lef/scaled/asap7sc7p5t_24_R_4x_170912.lef",
      "spice file": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/cdl/lvs/asap7_75t_R.cdl",
      "gds file": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24_R.gds",
      "qrc techfile": "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/qrc/qrcTechFile_typ03_scaled4xV06",
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

The file pointers, in this case, use the tarball prefix because Hammer will be extracting files directly from the ASAP7 tarball. This points Hammer to one part of the PDK.  The ``corner`` key tells Hammer what process and temperature corner that these files correspond to.  The ``supplies`` key tells Hammer what the nominal supply for these cells are.  The ``provides`` key has several sub-keys that tell Hammer what kind of library this is (examples include ``stdcell``, ``fiducials``,
``io pad cells``, ``bump``, and ``level shifters``) and the threshold voltage flavor of the cells, if applicable. Depending on the technology, adding the tech LEF for the technology with the ``lib_type`` set as ``technology`` may also be needed.

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
    {"name": "coreSite", "x": 0.216, "y": 1.08}
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
  ]

There are 8 ``cell_type`` s supported: ``tiehicell``, ``tielocell``, ``tiehilocell``, ``endcap``, ``iofiller``, ``stdfiller``, ``decap``, and ``tapcell``. Depending on the tech/tool, some of these cell types can only have 1 cell in the ``name`` list.

There is an optional ``size`` list. For each element in its corresponding ``name`` list, a size (type: str) can be given. An example of how this is used is for ``decap`` cells, where each listed cell has a typical capacitance, which a place and route tool can then use to place decaps to hit a target total decapacitance value. The ASAP7 technology doesn't have characterized decaps, but it would look like this:

.. code-block:: json

    {"cell_type": "decap", "name": ["DECAPx1_ASAP7_75t_R", "DECAPx1_ASAP7_75t_L", "DECAPx1_ASAP7_75t_SL", "DECAPx1_ASAP7_75t_SRAM", "DECAPx2_ASAP7_75t_R", "DECAPx2_ASAP7_75t_L", "DECAPx2_ASAP7_75t_SL", "DECAPx2_ASAP7_75t_SRAM", "DECAPx4_ASAP7_75t_R", "DECAPx4_ASAP7_75t_L", "DECAPx4_ASAP7_75t_SL", "DECAPx4_ASAP7_75t_SRAM", "DECAPx6_ASAP7_75t_R", "DECAPx6_ASAP7_75t_L", "DECAPx6_ASAP7_75t_SL", "DECAPx6_ASAP7_75t_SRAM", "DECAPx10_ASAP7_75t_R", "DECAPx10_ASAP7_75t_L", "DECAPx10_ASAP7_75t_SL", "DECAPx10_ASAP7_75t_SRAM"],
    "size": ["1 fF", "1 fF", "1 fF", "1 fF", "2 fF", "2 fF", "2 fF", "2 fF", "4 fF", "4 fF", "4 fF", "4 fF", "6 fF", "6 fF", "6 fF", "6 fF", "10 fF", "10 fF", "10 fF", "10 fF"]
    }
