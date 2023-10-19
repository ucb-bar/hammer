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
* Several output formats only run successfully when a power database is loaded from a checkpoint, the reason here being unclear.
  For the following output formats, start from the `report_power` step to generate the correct report (i.e. `make redo-power-rtl HAMMER_EXTRA_ARGS="--start_before_step report_power"`)
  * `ppa` - the underlying `report_ppa` will error out completely unless run after loading the checkpoint
  * `profile` - the underlying `plot_power_profile` and `dump_power_profile` commands will print the warning `Invalid frame name /stim#X/frame#X. No stimulus read. Using vectorless power computation`,
    despite already reading and computing power for this exact stimulus.
      * Another fix for this was reading each stimulus in non-append mode (i.e. without the `-append` flag), but the append mode drastically saves time when multiple report configs are specified for the same stimulus

