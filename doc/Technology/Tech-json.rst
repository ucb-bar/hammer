.. _tech-json:

Hammer Tech Config (Tech JSON)
===============================

Technology plugins must set up some general information about the install of the PDK, set up DRC rule decks, set up pointers to PDK files, and supply technology stackup information. 
Formerly, this information was provided in a static ``<tech_name>.tech.json`` file. We now encourage you to generate this information in the form of ``TechJSON`` Pydantic BaseModel instances (see ``hammer/tech/__init__.py`` for all BaseModel definitions). Instructions are given below for both forms, with examples from the Sky130 and ASAP7 plugins.

For the full schema of the tech configuration, please see the :ref:`full_schema` section below, which is derived from ``TechJSON``.

Technology Install
---------------------------------

The user may supply the PDK to Hammer as an already extracted directory and/or as a tarball that Hammer can automatically extract. Setting ``technology.TECH_NAME.<dir>`` key (as defined in the plugin's ``defaults.yml``) will fill in as the path prefix for paths supplied to PDK files.

Path prefixes can be supplied in multiple forms. The options are as follows (taken from ``prepend_dir_path`` in ``hammer/tech/__init__py``):

#. Absolute path: the path starts with "/" and refers to an absolute path on the filesystem
   * ``/path/to/a/lib/file.lib`` -> ``/path/to/a/lib/file.lib``
#. Tech plugin relative path: the path has no "/"s and refers to a file directly inside the tech plugin folder
   * ``techlib.lib`` -> ``<tech plugin package>/techlib.lib``
#. Tech cache relative path: the path starts with an identifier which is "cache" (this is used in the SKY130 example below)
   * ``cache/primitives.v`` -> ``<tech plugin cache dir>/primitives.v``
#. Install relative path: the path starts with an install/tarball identifier (installs.id, tarballs.root.id) and refers to a file relative to that identifier's path
   * ``pdkroot/dac/dac.lib`` -> ``/nfs/ecad/tsmc100/stdcells/dac/dac.lib``
#. Library extra_prefix path: the path starts with an identifier present in the provided library's ``extra_prefixes`` Field
   * ``lib1/cap150f.lib`` -> ``/design_files/caps/cap150f.lib``

Below is an example of the installs and tarballs defining path prefixes from the Sky130 and ASAP7 plugins.

Pydantic:

.. code-block:: python

  def gen_config(self) -> None:
      #...
      self.config = TechJSON(
          name = "Skywater 130nm Library",
          grid_unit = "0.001",
          installs = [
              PathPrefix(id = "$SKY130_NDA", path = "technology.sky130.sky130_nda"),
              PathPrefix(id = "$SKY130A", path = "technology.sky130.sky130A"),
              PathPrefix(id = "$SKY130_CDS", path = "technology.sky130.sky130_cds")
          ],
          #fields skipped...
        )

JSON:

.. code-block:: json

  "name": "ASAP7 Library",
  "grid_unit": "0.001",
  "installs": [
    {
      "id": "$PDK",
      "path": "technology.asap7.pdk_install_dir"
    },
    {
      "id": "$STDCELLS",
      "path": "technology.asap7.stdcell_install_dir"
    }
  ],
  "tarballs": [
    {
      "root": {
        "id": "ASAP7_PDK_CalibreDeck.tar",
        "path": "technology.asap7.tarball_dir"
      },
      "homepage": "http://asap.asu.edu/asap/",
      "optional": true
    }
  ],

The ``id`` field is used within the file listings further down in the file to prefix ``path``, as shown in detail below. If the file listing begins with ``cache``, then this denotes files that exist in the tech cache, which are generally placed there by the tech plugin's post-installation script (see ASAP7's ``post_install_script`` method). In the ASAP7 example, the encrypted Calibre decks are provided in a tarball and denoted as optional.

DRC/LVS Deck Setup
---------------------------------

As many DRC & LVS decks for as many tools can be specified in the ``drc decks`` and ``lvs decks`` keys. Additional DRC/LVS commands can be appended to the generated run files by specifying raw text in the ``additional_drc_text`` and ``additional_lvs_text`` keys. 

Pydantic:

.. code-block:: python

  def gen_config(self) -> None:
      #...
      self.config = TechJSON(
          #fields skipped...
          drc_decks = [
              DRCDeck(tool_name = "calibre", deck_name = "calibre_drc", path = "$SKY130_NDA/s8/V2.0.1/DRC/Calibre/s8_drcRules"),
              DRCDeck(tool_name = "klayout", deck_name = "klayout_drc", path = "$SKY130A/libs.tech/klayout/drc/sky130A.lydrc"),
              DRCDeck(tool_name = "pegasus", deck_name = "pegasus_drc", path = "$SKY130_CDS/Sky130_DRC/sky130_rev_0.0_1.0.drc.pvl")
          ],
          additional_drc_text = "",
          #fields skipped...
      )

The example above contains decks for 3 different tools, with file pointers using the installs prefixes defined before.

JSON:

.. code-block:: json

  "lvs_decks": [
    {
      "tool_name": "calibre",
      "deck_name": "all_lvs",
      "path": "ASAP7_PDK_CalibreDeck.tar/calibredecks_r1p7/calibre/ruledirs/lvs/lvsRules_calibre_asap7.rul"
    }
  ],
  "additional_lvs_text": "LVS SPICE EXCLUDE CELL \*SRAM*RW*\"\nLVS BOX \"SRAM*RW*\"\nLVS FILTER \*SRAM*RW*\" OPEN", 

The file pointers, in this case, use the tarball prefix because Hammer will be extracting the rule deck directly from the ASAP7 tarball. The additional text is needed to tell Calibre that the dummy SRAM cells need to be filtered from the source netlist and boxed and filtered from the layout.

Library Setup
---------------------------------

The ``libraries`` Field also must be set in the TechJSON instance. This will tell Hammer where to find all of the relevant files for standard cells and other blocks for the VLSI flow. Path prefixes are used most heavily here.

The ``corner`` Field (BaseModel type: Corner) tells Hammer what process and temperature corner that these files correspond to.  The ``supplies`` Field (BaseModel type: Supplies) tells Hammer what the nominal supply for these cells are.  
The ``provides`` Field (type: List[Provide]) has several sub-fields that tell Hammer what kind of library this is (examples include ``stdcell``, ``fiducials``, ``io pad cells``, ``bump``, and ``level shifters``) and the threshold voltage flavor of the cells, if applicable.
Adding the tech LEF for the technology with the ``lib_type`` set as ``technology`` is necessary for place and route. This must be the first ``lef_file`` provided in the entire list of Libraries.

Pydantic:

.. code-block:: python

  def gen_config(self) -> None:
      #...
      libs = [
          Library(lef_file = "cache/sky130_fd_sc_hd__nom.tlef", verilog_sim = "cache/primitives.v", provides = [Provide(lib_type = "technology")]),
          Library(spice_file = "$SKY130A/libs.ref/sky130_fd_io/spice/sky130_ef_io__analog.spice", provides = [Provide(lib_type = "IO library")])
      ]
      #...
      #Generate loops
      SKYWATER_LIBS = os.path.join('$SKY130A', 'libs.ref', library)
      for cornerfilename in lib_corner_files:
          #...
          lib_entry = Library(
              nldm_liberty_file =  os.path.join(SKYWATER_LIBS,'lib', cornerfilename),
              verilog_sim =        os.path.join(SKYWATER_LIBS,'verilog', file_lib + '.v'),
              lef_file =           lef_file,
              spice_file =         spice_file,
              gds_file =           os.path.join(SKYWATER_LIBS,'gds', gds_file),
              corner = Corner(
                  nmos = speed,
                  pmos = speed,
                  temperature = temp
              ),
              supplies = Supplies(
                  VDD = vdd,
                  GND  ="0 V"
              ),
              provides = [Provide(
                  lib_type = cell_name,
                  vt = "RVT"
                  )
              ]
          )
          libs.append(lib_entry)
      #...
      self.config = TechJSON(
          #fields skipped...
          libraries = libs,
          #fields skipped...
      )

In the above example, we use the ``$SKY130A`` prefix and some loops to generate Library entries. These loops are often derived from the directory structure of the standard cell library.

JSON:

.. code-block:: json

  "libraries": [
    {
      "lef_file": "$STDCELLS/techlef_misc/asap7_tech_4x_201209.lef",
      "provides": [
        {
          "lib_type": "technology"
        }
      ]
    },
    {
      "nldm_liberty_file": "$STDCELLS/LIB/NLDM/asap7sc7p5t_SIMPLE_RVT_TT_nldm_201020.lib.gz",
      "verilog_sim": "$STDCELLS/Verilog/asap7sc7p5t_SIMPLE_RVT_TT_201020.v",
      "lef_file": "$STDCELLS/LEF/scaled/asap7sc7p5t_27_R_4x_201211.lef",
      "spice_file": "$STDCELLS/CDL/LVS/asap7sc7p5t_27_R.cdl",
      "gds_file": "$STDCELLS/GDS/asap7sc7p5t_27_R_201211.gds",
      "qrc_techfile": "$STDCELLS/qrc/qrcTechFile_typ03_scaled4xV06",
      "spice_model_file": {
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

The file pointers, in this case, use the ``$PDK`` and ``$STDCELLS`` prefix as defined in the installs.  

.. _filters:

Library Filters
~~~~~~~~~~~~~~~

Library filters are defined in the ``LibraryFilter`` class in ``hammer/tech/__init__.py``. These allow you to filter the entire set of libraries based on specific conditions, such as a file type or corner. Additional functions can be used to extract paths, strings, sort, and post-process the filtered libraries.

For a list of pre-built library filters, refer to the properties in the ``LibraryFilterHolder`` class in the same file, accessed as ``hammer.tech.filters.<filter_method>``

Stackup
--------------------------------
The ``stackups`` sets up the important metal layer information for Hammer to use. All this information is typically taken from the tech LEF and can be automatically filled in with a script.

You can use ``LEFUtils.get_metals`` to generate the stackup information for simple tech LEFs:

.. code-block:: python

  from hammer.tech import *
  from hammer.utils import LEFUtils
  class SKY130Tech(HammerTechnology):
      def gen_config(self) -> None:
          #...
          stackups = []  # type: List[Stackup]
          tlef_path = os.path.join(SKY130A, 'libs.ref', library, 'techlef', f"{library}__min.tlef")
          metals = list(map(lambda m: Metal.model_validate(m), LEFUtils.get_metals(tlef_path)))
          stackups.append(Stackup(name = library, grid_unit = Decimal("0.001"), metals = metals))

          self.config = TechJSON(
              #fields skipped...
              stackups = stackups,
              #fields skipped...
          )


Below is an example of one metal layer in the ``metals`` list from the ASAP7 example tech plugin. This gives a better idea of the serialized fields in the Metal BaseModel. This is extracted by loading the tech LEF into Innovus, then using the ``hammer/par/innovus/dump_stackup_to_json.tcl`` script.

.. code-block:: json

        {"name": "M3", "index": 3, "direction": "vertical", "min_width": 0.072, "pitch": 0.144, "offset": 0.0, "power_strap_widths_and_spacings": [{"width_at_least": 0.0, "min_spacing": 0.072}], "power_strap_width_table": [0.072, 0.36, 0.648, 0.936, 1.224, 1.512]}

The metal layer name and layer number is specified. ``direction`` specifies the preferred routing direction for the layer. ``min_width`` and ``pitch`` specify the minimum width wire and the track pitch, respectively.  ``power_strap_widths_and_spacings`` is a list of pairs that specify design rules relating to the widths of wires and minimum required spacing between them. This information is used by Hammer when drawing power straps to make sure it is conforming to some basic design rules. 

        
Sites
--------------------------------
The ``sites`` field specifies the unit standard cell size of the technology for Hammer.

.. code-block:: python

  def gen_config(self) -> None:
      #...
      self.config = TechJSON(
          #fields skipped...
          sites = [
              Site(name = "unithd", x = Decimal("0.46"), y = Decimal("2.72")),
              Site(name = "unithddbl", x = Decimal("0.46"), y = Decimal("5.44"))
          ],
          #fields skipped...
      )

.. code-block:: json

  "sites": [
    {"name": "asap7sc7p5t", "x": 0.216, "y": 1.08}
  ]

These are examples from the Sky130 and ASAP7 tech plugin in which the ``name`` parameter specifies the core site name used in the tech LEF, and the ``x`` and ``y`` parameters specify the width and height of the unit standard cell size, respectively.

Special Cells
--------------------------------
The ``special_cells`` field specifies a set of cells in the technology that have special functions. 
The example below shows a subset of the Sky130 and ASAP7 tech plugin for 2 types of cells: ``tapcell`` and ``stdfiller``.

.. code-block:: python

  def gen_config(self) -> None:
      #...
      self.config = TechJSON(
          #fields skipped...
          special_cells = [
              SpecialCell(cell_type = CellType("tapcell"), name = ["sky130_fd_sc_hd__tapvpwrvgnd_1"]),
              SpecialCell(cell_type = CellType("stdfiller"), name = ["sky130_fd_sc_hd__fill_1", "sky130_fd_sc_hd__fill_2", "sky130_fd_sc_hd__fill_4", "sky130_fd_sc_hd__fill_8"]),
          ]
      )

.. code-block:: json

  "special_cells": [
    {"cell_type": "tapcell", "name": ["TAPCELL_ASAP7_75t_L"]},
    {"cell_type": "stdfiller", "name": ["FILLER_ASAP7_75t_R", "FILLER_ASAP7_75t_L", "FILLER_ASAP7_75t_SL", "FILLER_ASAP7_75t_SRAM", "FILLERxp5_ASAP7_75t_R", "FILLERxp5_ASAP7_75t_L", "FILLERxp5_ASAP7_75t_SL", "FILLERxp5_ASAP7_75t_SRAM"]},

See the ``SpecialCell`` subsection in the :ref:`full_schema` for a list of special cell types. Depending on the tech/tool, some of these cell types can only have 1 cell in the ``name`` list.

There is an optional ``size`` list. For each element in its corresponding ``name`` list, a size (type: str) can be given. An example of how this is used is for ``decap`` cells, where each listed cell has a typical capacitance, which a place and route tool can then use to place decaps to hit a target total decapacitance value. After characterizing the ASAP7 decaps using Voltus, the nominal capacitance is filled into the ``size`` list:

.. code-block:: json

    {"cell_type": "decap", "name": ["DECAPx1_ASAP7_75t_R", "DECAPx1_ASAP7_75t_L", "DECAPx1_ASAP7_75t_SL", "DECAPx1_ASAP7_75t_SRAM", "DECAPx2_ASAP7_75t_R", "DECAPx2_ASAP7_75t_L", "DECAPx2_ASAP7_75t_SL", "DECAPx2_ASAP7_75t_SRAM", "DECAPx2b_ASAP7_75t_R", "DECAPx2b_ASAP7_75t_L", "DECAPx2b_ASAP7_75t_SL", "DECAPx2b_ASAP7_75t_SRAM", "DECAPx4_ASAP7_75t_R", "DECAPx4_ASAP7_75t_L", "DECAPx4_ASAP7_75t_SL", "DECAPx4_ASAP7_75t_SRAM", "DECAPx6_ASAP7_75t_R", "DECAPx6_ASAP7_75t_L", "DECAPx6_ASAP7_75t_SL", "DECAPx6_ASAP7_75t_SRAM", "DECAPx10_ASAP7_75t_R", "DECAPx10_ASAP7_75t_L", "DECAPx10_ASAP7_75t_SL", "DECAPx10_ASAP7_75t_SRAM"], "size": ["0.39637 fF", "0.402151 fF", "0.406615 fF", "0.377040 fF","0.792751 fF", "0.804301 fF", "0.813231 fF", "0.74080 fF", "0.792761 fF", "0.804309 fF", "0.813238 fF","0.75409 fF", "1.5855 fF", "1.6086 fF", "1.62646 fF", "1.50861 fF", "2.37825 fF", "2.4129 fF", "2.43969 fF", "2.26224 fF", "3.96376 fF", "4.02151 fF", "4.06615 fF", "3.7704 fF"]},

Don't Use, Physical-Only Cells
--------------------------------
The ``dont_use_list`` is used to denote cells that should be excluded due to things like bad timing models or layout.
The ``physical_only_cells_list`` is used to denote cells that contain only physical geometry, which means that they should be excluded from netlisting for simulation and LVS. Examples:

.. code-block:: python

  def gen_config(self) -> None:
      #...
      self.config = TechJSON(
          #fields skipped...
          physical_only_cells_list = [
              "sky130_fd_sc_hd__tap_1", "sky130_fd_sc_hd__tap_2", "sky130_fd_sc_hd__tapvgnd_1", "sky130_fd_sc_hd__tapvpwrvgnd_1",
              "sky130_fd_sc_hd__fill_1", "sky130_fd_sc_hd__fill_2", "sky130_fd_sc_hd__fill_4", "sky130_fd_sc_hd__fill_8",
              "sky130_fd_sc_hd__diode_2"]
          dont_use_list = [
              "*sdf*",
              "sky130_fd_sc_hd__probe_p_*",
              "sky130_fd_sc_hd__probec_p_*"
          ]
          #fields skipped...
      )

.. code-block:: json

  "dont_use_list": [
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
  "physical_only_cells_list": [
    "TAPCELL_ASAP7_75t_R", "TAPCELL_ASAP7_75t_L", "TAPCELL_ASAP7_75t_SL", "TAPCELL_ASAP7_75t_SRAM",
    "TAPCELL_WITH_FILLER_ASAP7_75t_R", "TAPCELL_WITH_FILLER_ASAP7_75t_L", "TAPCELL_WITH_FILLER_ASAP7_75t_SL", "TAPCELL_WITH_FILLER_ASAP7_75t_SRAM",
    "FILLER_ASAP7_75t_R", "FILLER_ASAP7_75t_L", "FILLER_ASAP7_75t_SL", "FILLER_ASAP7_75t_SRAM", 
    "FILLERxp5_ASAP7_75t_R", "FILLERxp5_ASAP7_75t_L", "FILLERxp5_ASAP7_75t_SL", "FILLERxp5_ASAP7_75t_SRAM"
  ],

.. _full_schema:

Full Schema
-----------

Note that in the the schema tables presented below, items with ``#/definitions/<class_name>`` are defined in other schema tables. This is done for documentation clarity, but in your JSON file, those items would be hierarchically nested.

.. jsonschema:: schema.json
   :lift_definitions:
