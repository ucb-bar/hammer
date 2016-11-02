# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# Looks at this system to determine what sort of scheduler should be used to
# run jobs.
ifneq ($(wildcard /usr/bin/srun),)
SCHEDULER_ADDON = src/addons/scheduler/slurm/
else ifneq ($(wildcard /tools/support/lsf/9.1/linux2.6-glibc2.3-x86_64/bin/bsub),)
SCHEDULER_ADDON = src/addons/scheduler/lsf/
else
SCHEDULER_ADDON = src/addons/scheduler/local/
endif

include $(SCHEDULER_ADDON)/vars.mk
