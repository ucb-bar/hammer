#  hammer-vlsi
#  CLI script - by default, it just uses the default CLIDriver.
#
#  See LICENSE for licence details.
'''
from hammer.vlsi import CLIDriver

def main():
    CLIDriver().main()

'''
import re
import os
import subprocess
import sys

# Add the parent directory to the Python path to allow imports from 'vlsi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vlsi')))

from hammer.vlsi import CLIDriver

import pdb
pdb.set_trace()

# minimal flow configuration variables
design = os.getenv('design', 'pass')
pdk = os.getenv('pdk', 'sky130')
tools = os.getenv('tools', 'nop')
env = os.getenv('env', 'bwrc')
extra = os.getenv('extra', '')  # extra configs
args = os.getenv('args', '')  # command-line args (including step flow control)
vlsi_dir = os.path.abspath('../e2e/')
OBJ_DIR = os.getenv('OBJ_DIR', f"{vlsi_dir}/build-{pdk}-{tools}/{design}")
# non-overlapping default configs
ENV_YML = os.getenv('ENV_YML', f"configs-env/{env}-env.yml")
PDK_CONF = os.getenv('PDK_CONF', f"configs-pdk/{pdk}.yml")
TOOLS_CONF = os.getenv('TOOLS_CONF', f"configs-tool/{tools}.yml")

# design-specific overrides of default configs
DESIGN_CONF = os.getenv('DESIGN_CONF', f"configs-design/{design}/common.yml")
DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"configs-design/{design}/{pdk}.yml")
makecmdgoals = os.getenv('MAKECMDGOALS', sys.argv[1]) ##This should be our target. Build is passed in
SIM_CONF = os.getenv('SIM_CONF',
    f"configs-design/{design}/sim-rtl.yml" if '-rtl' in makecmdgoals else
    f"configs-design/{design}/sim-syn.yml" if '-syn' in makecmdgoals else
    f"configs-design/{design}/sim-par.yml" if '-par' in makecmdgoals else ''
)
POWER_CONF = os.getenv('POWER_CONF',
    f"configs-design/{design}/power-rtl-{pdk}.yml" if 'power-rtl' in makecmdgoals else
    f"configs-design/{design}/power-syn-{pdk}.yml" if 'power-syn' in makecmdgoals else
    f"configs-design/{design}/power-par-{pdk}.yml" if 'power-par' in makecmdgoals else ''
)
PROJ_YMLS = [PDK_CONF, TOOLS_CONF, DESIGN_CONF, DESIGN_PDK_CONF, SIM_CONF, POWER_CONF, extra]
#PROJ_YMLS = ' '.join([PDK_CONF, TOOLS_CONF, DESIGN_CONF, DESIGN_PDK_CONF, SIM_CONF, POWER_CONF, extra]) #Shouldn't be a list, changes format from Makefile
HAMMER_EXTRA_ARGS = ' '.join([f"-p {conf}" for conf in PROJ_YMLS if conf]) + f" {args}"
HAMMER_D_MK = os.getenv('HAMMER_D_MK', f"{OBJ_DIR}/hammer.d")

#These functions don't really make sense
def build():
    print(f"Build command would run here with OBJ_DIR: {OBJ_DIR}")
    # can add logic to run for the build here
def clean():
    if os.path.exists(OBJ_DIR):
        subprocess.run(f"rm -rf {OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)

def main():
    if 'clean' in sys.argv:
        clean()
    else:
        build()
    # Proceed with the default CLIDriver
    CLIDriver().main()
if __name__ == '__main__':
    #sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    #Adds configuration to system arguments, so they are visible to ArgumentParser
    HAMMER_EXTRA_ARGS_split = HAMMER_EXTRA_ARGS.split()
    for arg in ['--obj_dir', OBJ_DIR, '-e', ENV_YML]:
        sys.argv.append(arg)
    for arg in HAMMER_EXTRA_ARGS_split:
        sys.argv.append(arg)
    sys.exit(main())

#Use the makecmdgoals variable to determine which function will be accessed
#Need to know how the hammer-vlsi command works with make build. Refer to graphic
