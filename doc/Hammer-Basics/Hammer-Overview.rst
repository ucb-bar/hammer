Hammer Overview
================================

Hammer has a set of actions and automatically takes the output of one action and converts it into the input for another.  For instance, a synthesis action will output a mapped verilog file which will then automatically by piped to the P&R input when a P&R action is called. 

A user's Hammer environment is typically separated into four different components: main Hammer, a tool plugin, a technology plugin, and a set of project specific Hammer input. Hammer is meant to expose a set of generalized APIs that are then implemented by tool and technology specific plugins.

Hammer is included in a larger project called `Chipyard <https://github.com/ucb-bar/chipyard>`__ which is the unified repo for an entire RTL, simulation, emulation, and VLSI flow from Berkeley Architecture Research. There is an in-depth Hammer demo there and is a great place to look at a typical Hammer setup.

Main Hammer
-------------------------------

Hammer provides the Python backend for a Hammer project and exposes a set of APIs that are typical of modern VLSI flows. These APIs are then implemented by a tool plugin and a technology plugin of the designer's choice. The structure of Hammer is meant to enable re-use and portability between technologies.

Hammer takes its inputs and serializes its state in form of YML and JSON files. The designer sets a variety of settings in the form of keys in different namespaces that are designated in Hammer to control its functionality. These keys are contained in ``hammer/src/hammer-vlsi/defaults.yml``. This file shows all of the keys that are a part of main Hammer and provides sensible defaults that may be overridden or are set to null if they must be provided by the designer.

Here is an example of a snippet that would be included in the user's input configuration.

.. _library-example:
.. code-block:: yaml

    vlsi.core.technology: "asap7"
    vlsi.inputs.supplies:
        VDD: "0.7 V"
        GND: "0 V"

This demonstrates two different namespaces, ``vlsi.core`` and ``vlsi.inputs``, and then two different keys, ``technology`` and ``supplies``, which are set to the ``asap7`` technology and to 0.7V supply voltage, respectively. 

Tech Plugins
-------------------------------

A techonology plugin consists of two files: a ``tech.json`` and a ``defaults.yml``.  The ``tech.json`` points Hammer to all of the required PDK files and the ``defaults.yml`` fills in some default keys reqgarding the technology for Hammer to consume. An example of this is shown in ``hammer/src/hammer-vlsi/technology/asap7/`` and how to setup a technology plugin is documented in more detail in the Technology portion of the docs.

Tool Plugins
-------------------------------

A Hammer tool plugin actually implements tool specific steps of the VLSI flow in Hammer. It generates tool specific inputs (in the form of TCL) by combining the designer's inputs with information from the technology plugin using the functionality of the Hammer backend.

There are already three Hammer tool plugin repos to which access may be granted to users of Hammer, pending approval from each tool vendor. These repos are ``hammer-cadence-plugins``, ``hammer-synopsys-plugins``, and ``hammer-mentor-plugins``. In them are tool plugin implementations for actions including synthesis, P&R, DRC, LVS, and simulation.

These plugins implement many required steps of a modern physical design flow. However, as VLSI designers know, in any real flow there are lots of very custom settings used and required elements of a flow that may not have direct analogs between technology nodes. To deal with this, Hammer has a very simple interface for the designer to create what are called hooks. Hooks are custom snippets that are can be inserted before or after any step in an action, or even replace one. This allows the
designer to leverage the APIs built into Hammer while easily inserting custom steps into the flow. Hooks are discussed in more detail in the Example Usage portion of the Hammer documentation. 

Calling Hammer
-------------------------------

After setting up the environment, Hammer is ready to use. Here is an example of a typical Hammer call:

.. _call-example:
.. code-block:: bash

    hammer-vlsi -e env.yml -p config.yml --obj_dir build par

Calling ``hammer-vlsi`` is the entry point into Hammer. An environment configuration is passed to Hammer using a ``-e`` flag, in this case ``env.yml``. ``env.yml`` points to the required licenses to run the desired tools. Any number of other YML or JSON files can then be passed in using the ``-p`` flag. In this case, there is only one, ``config.yml``, and it needs to set all the required keys for the step of the flow being run.  ``--obj_dir build`` designates what directory Hammer
should work in and write all of its outputs to. Finally, ``par`` designates that this is a place-and-route action.  In this case, Hammer will write outputs to the path ``CURRENT_DIR/build/par-rundir``.

