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
          vlsi.core...
          vlsi.inputs...
      - ModuleA:
          vlsi.core...
          vlsi.inputs...
      - ModuleAA:
          vlsi.core...
          vlsi.inputs...

Note how the configuration specific to each module in ``vlsi.inputs.hierarchical.constraints`` appears like they would in a flat flow. This means you can apply meta directives to them as normal, as long as the references are in the same parent dictionary (i.e., key = module name).
If you have constraints for the same module in multiple files, you can use ``vlsi.inputs.hierarchical.constraints_meta: append`` and the constraints will be combined properly.

.. note::
    In a bottom-up hierarchical flow, submodule instances must have ``type: hardmacro`` in ``vlsi.inputs.placement_constraints`` because they are hardened from below.

Special considerations for legacy support:

* If each module's ``constraints`` is a list of dicts with a single key/value pair, meta actions are not supported and the entire project configuration must be specified in a single file.

* If placement constraints are specified with ``vlsi.inputs.hierarchical.manual_placement_constraints``, all of a given module's placement constraints must be specified in a single file.

Flow Management and Actions
---------------------------

Based on the structure in ``vlsi.inputs.hierarchical.manual_modules``, Hammer constructs a hierarchical flow graph of dependencies. In this particular example, synthesis and place-and-route of ``ModuleAA`` will happen first. Synthesis of ``ModuleA`` will then depend on the place-and-route output of ``ModuleAA``, and so forth.

These are enumerated in the auto-generated Makefile, ``hammer.d``, which is placed in the directory pointed to by the ``--obj_dir`` command line flag when the ``buildfile`` action is run. This action must be run BEFORE executing your flow. If you adjust the hierarchy, you must re-run this action.

To perform a flow action (syn, par, etc.) for a module using the auto-generated Makefile, the name of the action is appended with the module name. For example, the generated Make target for synthesis of ``ModuleA`` is ``syn-ModuleA``. A graphical example of the auto-generated dependency graph with ``RocketTile`` under a ``ChipTop`` is shown below:

.. image:: hier.svg

The auto-generated Makefile also has ``redo-`` targets corresponding to each generated action, e.g. ``redo-syn-ModuleA``. These targets break the dependency graph and allow you to re-run any action with new input configuration without forcing the flow to re-run from the beginning of the graph.

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

#. Hammer IR keys specified at the root level (i.e. outside of ``vlsi.inputs.hierarchical.constraints``) are overridden by the corresponding submodule constraints. Generally, to avoid confusion, it is recommended to specify all constraints module-by-module with ``vlsi.inputs.hierarchical.constraints``.

#. Most Hammer APIs are not yet intelligent enough to constrain across hierarchical boundaries. For example:

    * The power straps API is unable to pitch match power straps based on legalized placement of submodule instances or vice versa.

    * The pin placement API does not match the placement of pins that may face each other in two adjacent submodule instances. You will need to either manually place the pins yourself or ensure a sufficient routing channel between the instances at the parent level.

#. Hammer does not support running separate decks for submodule DRC and LVS. Technology plugins may need to be written with Makefiles and/or technology-specific options that will implement different checks for submodules vs. the  top level.
