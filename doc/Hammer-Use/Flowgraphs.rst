.. _flowgraphs:

Flowgraphs
==========

Hammer has **experimental** support for flowgraph constructions, similar to tools like `mflowgen <https://github.com/mflowgen/mflowgen>`_.
Their intention is to simplify the way flows are constructed and ran in Hammer.
They can be imported via the ``hammer.flowgraph`` module.

Construction
------------

Flowgraphs are consist of a collection of ``Node`` instances linked together via a ``Graph`` instance.
Each ``Node`` "pulls" from a directory to feed in inputs and "pushes" output files to another directory to be used by other nodes.
``Node`` instances are roughly equivalent to a single call to the ``hammer-vlsi`` CLI tool, so they take in similar attributes:

* The action being called
* The tool used to perform the action
* The pull and push directories
* Any *required* input/output files
* Any *optional* input/output files (the name of the *first* output file corresponds to the name of the JSON that the action emits)
* A driver to run the node with; this enables backwards compatibility with :ref:`hooks <hooks>`.
* Options to specify steps within an action; this enables backwards compatibility with :ref:`flow control <flow-control>`.

    * ``start_before_step``
    * ``start_after_step``
    * ``stop_before_step``
    * ``stop_after_step``
    * ``only_step``

A minimal example of a ``Node``:

.. code-block:: python
    
    from hammer.flowgraph import Node

    test = Node(
        action="foo",
        tool="nop",
        pull_dir="foo_dir",
        push_dir="/dev/null",
        required_inputs=["foo.yml"],
        required_outputs=["foo-out.json"],
    )

Each ``Node`` has the ability to be "privileged", meaning that a flow *must* start with this node.
This only occurs when a flow is being controlled using any of the steps.

Running a Flowgraph
-------------------

``Node`` instances are linked together using an `adjacency list <https://en.wikipedia.org/wiki/Adjacency_list>`_.
This list can be used to instantiate a ``Graph``:

.. code-block:: python

    from hammer.flowgraph import Graph, Node

    root = Node(
        "foo", "nop", "foo_dir", "",
        ["foo.yml"],
        ["foo-out.json"],
    )
    child1 = Node(
        "bar", "nop", "foo_dir", "bar_dir",
        ["foo-out.json"],
        ["bar-out.json"],
    )
    graph = Graph({root: [child1]})

Using the Hammer CLI tool, separate actions are manually linked via an *auxiliary* action, such as ``syn-to-par``.
By using a flowgraph, ``Graph`` instances by default *automatically* insert auxiliary actions.
This means that actions no longer need to be specified in a flow; the necessary nodes are inserted by the flowgraph tool.
This feature can be disabled by setting ``auto_auxiliary`` to ``False`` in a ``Graph``.

A ``Graph`` can be run by calling the ``run`` method and passing in a starting node.
When running a flow, each ``Node`` keeps an internal status based on the status of the action being run:

* ``NOT_RUN``: The action has yet to be run.
* ``RUNNING``: The action is currently running.
* ``COMPLETE``: The action has finished.
* ``INCOMPLETE``: The action ran into an error while being run.
* ``INVALID``: The action's outputs have been invalidated (e.g. inputs or attributes have changed).

The interactions between the statuses are described in the following state diagram:

.. mermaid::

    stateDiagram-v2
        [*] --> NOT_RUN
        NOT_RUN --> RUNNING
        RUNNING --> INCOMPLETE
        RUNNING --> COMPLETE
        INCOMPLETE --> NOT_RUN
        COMPLETE --> INVALID
        INVALID --> NOT_RUN

Regardless of whether a flow completes with or without errors, the graph at the time of completion or error is returned, allowing for a graph to be "resumed" once any errors have been fixed.

Visualization
-------------

A flowgraph can be visualized in Markdown files via the `Mermaid <https://mermaid.js.org/>`_ tool.
Calling a ``Graph`` instance's ``to_mermaid`` method outputs a file named ``graph-viz.md``.
The file can be viewed in a site like `Mermaid's live editor <https://mermaid.live/>`_ or using Github's native support.

The flowgraph below would appear like this:

.. code-block:: python

    from hammer.flowgraph import Graph, Node

    syn = Node(
        "syn", "nop",
        os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
        ["syn-in.yml"],
        ["syn-out.json"],
    )
    s2p = Node(
        "syn-to-par", "nop",
        os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
        ["syn-out.json"],
        ["s2p-out.json"],
    )
    par = Node(
        "par", "nop",
        os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
        ["s2p-out.json"],
        ["par-out.json"],
    )
    g = Graph({
        syn: [s2p],
        s2p: [par],
        par: []
    })


Here are the contents of ``graph-viz.md`` after calling ``g.to_mermaid()``:

.. code-block:: markdown

    ```mermaid
    
    stateDiagram-v2
        syn --> syn_to_par
        syn_to_par --> par
    ```

Which would render like this:

.. mermaid::

    stateDiagram-v2
        syn --> syn_to_par
        syn_to_par --> par

Note that the separators have been changed to comply with Mermaid syntax.

Caveats
-------

The flowgraph frontend has a number of caveats that prevent it from full parity with the current CLI tool:

* If flows are constructed in a Python interactive session, then errors from the underlying tool do *not* propagate to the flowgraph and thus render the interactive session unusable.
  This can be worked around by embedding the flow in a Python script and running it from the command line.
