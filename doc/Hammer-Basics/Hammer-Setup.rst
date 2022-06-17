Hammer Setup
=============================

Hammer has a few requirements and there are several environment variables to setup.

System Requirements
-----------------------------
- Python 3.6+ recommended (minimum Python 3.3+)

-- For Python 3.4 and lower, the ``typing`` module must be installed. (``python3 -m pip install typing``)

-- For Python 3.4, the enum34 package must be installed. (``python3 -m pip install enum34``)

- python3 in the $PATH

- hammer-shell in the $PATH

- hammer_config, python-jsonschema-objects, hammer-tech, hammer-vlsi in $PYTHONPATH

- HAMMER_PYYAML_PATH set to pyyaml/lib3 or pyyaml in $PYTHONPATH

- HAMMER_HOME set to hammer repo root

- HAMMER_VLSI path set to $HAMMER_HOME/src.hammer-vlsi

Sourcing ``hammer/sourceme.sh`` will setup the environment described above.

To check your environment you may run the following:

.. _library-example:
.. code-block:: bash

    git submodule update --init --recursive
    export HAMMER_HOME=$PWD
    source sourceme.sh
    cd src/test
    ./unittests.sh
    echo $?

If the last line above returns 0, then the environment is set up and ready to go.

Note: certain tools and technologies will have additional system requirements. For example, LVS with Netgen requires Tcl/Tk 8.6, which is not installed for CentOS7/RHEL7 and below. Refer to each respective tool and technology's documentation for those requirements.
