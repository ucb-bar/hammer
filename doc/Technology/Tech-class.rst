Hammer Technologies
===================

Hammer currently has open-source technology plugins in the ``hammer/technology`` folder. Other proprietary technology plugins cannot be made public without 3-way NDAs or special agreements with their respective foundries.

The structure of each technology plugin package is as follows:

* hammer

    * TECHNOLOGY_NAME

        * ``__init__.py`` contains the tech class object and methods for PDK installation/extraction and getting :ref:`hooks<hooks>`.
        * ``<name>.tech.json`` contains the static information about the technology. See the section :ref:`tech-json` for a guide.
        * ``defaults.yml`` contains the default tech-specific :ref:`config`. See the section :ref:`tech-defaults` for a guide.

        * ACTION_NAME

            * ``__init__.py`` (optional) can contain a technology's implementation of an action. Commonly, this is used for the SRAM compilation action.

            * TOOL_NAME

                * ``__init__.py`` (optional) contains callable :ref:`hook<hooks>` methods specific to the technology and tool, if there are too many to put in TECHNOLOGY_NAME/__init__.py. 

Resources that are needed may go in this directory structure where necessary.

HammerTechnology Class
----------------------

The HammerTechnology class is the base class that all technology plugins should inherit from and is defined in ``hammer/tech/__init__.py``. Particularly useful methods are:

* ``gen_config``: the plugin subclass should override this method to generate the tech config. See the next section (:ref:`tech-json`) for details.
* ``post_install_script``: the plugin subclass should override this method to apply any non-default PDK installation steps or hotfixes in order to set up the technology libraries for use with Hammer.
* ``read_libs``: this is a particularly powerful method to read the libraries contained in the ``tech.json`` file and filter them using the filters also contained the same file. See the :ref:`filters` section for details.
* ``get_tech_<action>_hooks``: these methods are necessary if tech--specific hooks are needed, and must return a list of hooks when a given tool name implementing the relevant action is called. Refer to the :ref:`hooks` section for details about how to write hooks. 
