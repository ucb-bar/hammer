# DRC/LVS with IC Validator

IC Validator is very command-line driven. Here are some usage notes:

* Many PDK decks will use variables to control switches. These are defined on command line with `-D` and can be defined in Hammer config using the `<drc/lvs>.icv.defines` key (type: List[Dict[str, str]]).
* Any deck directories that need to be included are defined on command line with `-I` and can be defined in Hammer config using the `<drc/lvs>.icv.include_dirs` key (type: List[str]).
* Extensibility is enabled by passing a file to the icv command with `-clf`. This file contains additional command line arguments, and is generated in the `generate_<drc/lvs>_args_file` step (can be overridden).
* Decks are included using the `generate_<drc/lvs>_run_file` step (can be overridden with additional ICV method calls).
* Results/violations are generated in a format readable by VUE (interactive violation browser) using the `-vue` option.
* Layout is viewed using IC Validator Workbench (ICVBV). It can communicate with VUE to generate violation markers by opening up a socket to ICV. The socket number can range between 1000 and 65535 (selectable by `<drc/lvs>.icv.icvwb_port`. Running the `generated_scripts/view_<drc/lvs>` script will handle this automatically, by starting ICVWB, opening the port, waiting for it to be listening, and then starting VUE.
* ICVWB layer mapping can be specified in `synopsys.layerprops` key.

Tested with:

* hammer-intech22-plugin
