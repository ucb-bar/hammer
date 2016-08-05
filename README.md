PLSI: Palmer's VLSI Scripts
---------

This repository contains my VLSI scripts.  These are designed to be highly
automated and portable to multiple technologies, vendors, and generators.  The
entire process is driven by a top-level Makefile.

To submit a bug report, run something like

 $ make SOC_GENERATOR=bar-testchip bugreport |& tee buginfo.txt

and then submit the bug report to me so I can see what's going on.  Be sure to
your make variables correctly when submitting the report!
