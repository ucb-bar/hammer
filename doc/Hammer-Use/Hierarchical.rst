.. _hierarchical:

Hierarchical Hammer Flow
============================================

Hammer supports a bottom-up hierarchical flow. This is beneficial for very large designs to reduce the computing power by partitioning it into submodules, especially if there are many repeated instances of those modules.

Hierarchical Hammer Config
--------------------------

The hierarchal flow is controlled in the ``vlsi.inputs.hierarchal`` namespace. To specify hierarchical mode, you must specify the following keys. In this example, we have our top module set as ``ChipTop``, with a submodule ``ModuleA`` and another submdule ``ModuleAA`` below that (these are names of Verilog modules).

.. code-block:: yaml
    
    vlsi.inputs.hierarchical:
      mode: hierarchical
      top_module: ChipTop
      config_source: manual
      manual_modules:
      - ChipTop:
        - ModuleA
      - ModuleA:
        - ModuleAA
      constraints:
      - ChipTop:
        - vlsi.core...
        - vlsi.inputs...
      - ModuleA:
        - vlsi.core...
        - vlsi.inputs...
      - ModuleAA:
        - vlsi.core...
        - vlsi.inputs...

Note how the configuration specific to each module in ``vlsi.inputs.hierarchical.constraints`` are list items, whereas in a flat flow, they would be at the root level.

Placement constraints for each module, however, are not specified here. Instead, they should be specified in ``vlsi.inputs.hierarchical.manual_placement_constraints``. The parameters such as ``x``, ``y``, ``width``, ``height``, etc. are omitted from each constraint for clarity. In the bottom-up hierarchal flow, instances of submodules are of ``type: hardmacro`` because they are hardened from below.

.. code-block:: yaml

    vlsi.inputs.hierarchical:
      manual_placement_constraints_meta: append
      manual_placement_constraints:
      - ChipTop:
        - path: "ChipTop"
          type: toplevel
        - path: "ChipTop/path/to/instance/of/ModuleA"
          type: hardmacro
      - ModuleA:
        - path: "ModuleA"
          type: toplevel
        - path: "ModuleA/path/to/instance/of/ModuleAA"
          type: hardmacro
      - ModuleAA:
        - path: "moduleAA"
          type: toplevel

Flow Management and Actions
---------------------------

Based on the structure in ``vlsi.inputs.hierarchical.manual_modules``, Hammer constructs a hierarchical flow graph of dependencies. In this particular example, synthesis and place-and-route of ``ModuleAA`` will happen first. Syntheis of ``ModuleA`` will then depend on the place-and-route output of ``ModuleAA``, and so forth. These are enumerated in the auto-generated Makefile.

To perform a flow action (syn, par, etc.) for a module using the auto-generated Makefile, the name of the action is appended with the module name. For example, the generated Make target for synthesis of ``ModuleA`` is ``syn-ModuleA``.

Cadence Implementation
----------------------

Currently, the hierarchical flow is implemented with the Cadence plugin using its Interface Logic Model (ILM) methodology. At the end of each submodule's place-and-route, an ILM is written as the hardened macro, which contains an abstracted view of its design and timing models only up to the first sequential element.

ILMs are similar to LEFs and LIBs for traditional hard macros, except that the interface logic is included in all views. This means that at higher levels of hierarchy, the ILM instances can be flattened at certain steps, such as those that perform timing analysis on the entire design, resulting in a more accurate picture of timing than a normal LIB would afford.

Tips for Constraining Hierarchical Modules
------------------------------------------

In a bottom-up hierarchical flow, is is important to remember that submodules do not know the environment in which they will placed. This means:

* At minimum, the pins must be placed on the correct edges of the submodule on metal layers that are accessible in the parent level. Depending on the technology, this may interfere with things like power straps near the edge, so custom obstructions may be necessary. If fixed IOs are placed in submodules (e.g. bumps), then in the parent level, those pins must be promoted up using the ``preplaced: true`` option in the pin assignment.

* Clocks should be constrained more tightly for a submodule compared to its parent to account for extra clock insertion delay, jitter, and skew at increasingly higher levels of hierarchy. Otherwise, you may run into surprise timing violations in submodule instances even if those passed timing in isolation.

* You may need to specify pin delays ``vlsi.inputs.delays`` for many pins to optimize the partitioning of sequential signals that cross the submodule boundary. By default, without pin delay constraints, the input and output delay are constrained to be coincident with its related clock arrival at the module boundary.

* Custom SDC constraints that originate from a higher level (e.g. false paths from async inputs) need to be specified in submodules as well.

* Custom CPFs will need to be written if differently-named power nets need to globally connected between submodules. Similarly, hierarchical flow with custom CPFs can also be used to fake a multi-power domain topology until Hammer properly supports this feature.

Special Notes & Limitations
---------------------------

#. Hammer IR keys propagate up through the hierarchical tree. For example, if ``vlsi.inputs.clocks`` was specified in the constraints for ``ModuleAA`` but not for ``ModuleA``, ``ModuleA`` will inherit ``ModuleAA``'s constraints. Take special care of where your constraints come from, especially for a parent module with more than one submodule. To avoid confusion, it is recommended to specify the same set of keys for every module.

#. Hammer IR keys specified at the root level (i.e. outside of ``vlsi.inputs.hierarchical.constraints``) do not override the corresponding submodule constraints. However, if you add a Hammer IR file using ``-p`` on the command line (after the file containing ``vlsi.inputs.hierarchical.constraints``), those keys are global and override submodule constraints unless a meta action is specified. To avoid confusion, it is recommended to specify all constraints with ``vlsi.inputs.hierarchical.constraints``.

#. Due to the structure of ``vlsi.inputs.hierarchical.constraints`` as a list structure, currently, there are the following limitations:

    * You must include all of the constraints in a single file. The config parser is unable to combine constraints from differnt files because most meta actions do not work on list items (advanced users will need to use ``deepsubst``). This will make it harder for collaboration, and unfortunately, changes to module constraints at a higher level of hierarchy after submodules are hardened will trigger the Make dependencies, so you will need to modify the generated Makefile or use redo-targets.

    * Other issues have been observed, such as the bump API failing (see `this issue <https://github.com/ucb-bar/hammer/issues/401>`_ at the top module level. This is caused by similar mechanisms as above. The workaround is to ensure that bumps are specified at the root level for only the top module and the bumps step is removed from submodule par actions.

#. Most Hammer APIs are not yet intelligent enough to constrain across hierarchical boundaries. For example:

    * The power straps API is unable to pitch match power straps based on legalized placement of submodule instances or vice versa.

    * The pin placement API does not match the placement of pins that may face each other in two adjacent submodule instances. You will need to either manually place the pins yourself or ensure a sufficient routing channel between the instances at the parent level.

#. Hammer does not support running separate decks for submodule DRC and LVS. Technology plugins may need to be written with Makefiles and/or technology-specific options that will implement different checks for submodules vs. the  top level.
