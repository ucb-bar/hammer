Cadence Joules RTL Power Tool Plugin
====================================

Tool Steps
----------

See ``__init__.py`` for the implementation of these steps.

    init_design
    synthesize_design
    report_power


A variety of different output reports may be generated with this tool.
Within the [Hammer default configs file](https://github.com/ucb-bar/hammer/blob/joules-fixes/hammer/config/defaults.yml),
the `power.inputs.report_configs` struct description
contains a summary of the different reporting options, specified via the `output_formats` struct field.

Known Issues
------------

* Joules supports saving the read stimulus file to the SDB (stimulus database) format via the `write_sdb` command. However, subsequent reads of this SDB file via the `read_sdb` command fail for no apparent reason
  * As a result, `read_stimulus`/`compute_power` cannot be a separate step in the plugin, because there is no way to save the results of these commands before running the various power reporting commands.
    Thus these two commands are run as part of the `report_power` step.
  * NOTE: this might not be a problem anymore with the new Joules version, so we should re-try this!!
