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
import json

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain
from airflow.decorators import task, dag
from datetime import datetime, timedelta

# Add the parent directory to the Python path to allow imports from 'vlsi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vlsi')))

from hammer.vlsi import CLIDriver
from hammer.vlsi.cli_driver import import_task_to_dag
#import pdb
#pdb.set_trace()
class AIRFlow:
    def __init__(self):
        #pdb.set_trace()
        # minimal flow configuration variables
        self.design = os.getenv('design', 'gcd')
        self.pdk = os.getenv('pdk', 'sky130')
        self.tools = os.getenv('tools', 'cm')
        self.env = os.getenv('env', 'bwrc')
        self.extra = os.getenv('extra', '')  # extra configs
        self.args = os.getenv('args', '')  # command-line args (including step flow control)
        self.vlsi_dir = os.path.abspath('../e2e/')
        self.OBJ_DIR = os.getenv('OBJ_DIR', f"{self.vlsi_dir}/build-{self.pdk}-{self.tools}/{self.design}")
        
        # non-overlapping default configs
        self.ENV_YML = os.getenv('ENV_YML', f"configs-env/{self.env}-env.yml")
        self.PDK_CONF = os.getenv('PDK_CONF', f"configs-pdk/{self.pdk}.yml")
        self.TOOLS_CONF = os.getenv('TOOLS_CONF', f"configs-tool/{self.tools}.yml")

        # design-specific overrides of default configs
        self.DESIGN_CONF = os.getenv('DESIGN_CONF', f"configs-design/{self.design}/common.yml")
        self.DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"configs-design/{self.design}/{self.pdk}.yml")
        
        # This should be your target, build is passed in
        
        #sys.argv[2] = "build"
        #self.makecmdgoals = os.getenv('MAKECMDGOALS', sys.argv[2])
        self.makecmdgoals = os.getenv('MAKECMDGOALS', "build")
        
        # simulation and power configurations
        self.SIM_CONF = os.getenv('SIM_CONF',
            f"configs-design/{self.design}/sim-rtl.yml" if '-rtl' in self.makecmdgoals else
            f"configs-design/{self.design}/sim-syn.yml" if '-syn' in self.makecmdgoals else
            f"configs-design/{self.design}/sim-par.yml" if '-par' in self.makecmdgoals else ''
        )
        self.POWER_CONF = os.getenv('POWER_CONF',
            f"configs-design/{self.design}/power-rtl-{self.pdk}.yml" if 'power-rtl' in self.makecmdgoals else
            f"configs-design/{self.design}/power-syn-{self.pdk}.yml" if 'power-syn' in self.makecmdgoals else
            f"configs-design/{self.design}/power-par-{self.pdk}.yml" if 'power-par' in self.makecmdgoals else ''
        )

        # create project configuration
        self.PROJ_YMLS = [self.PDK_CONF, self.TOOLS_CONF, self.DESIGN_CONF, self.DESIGN_PDK_CONF, self.SIM_CONF, self.POWER_CONF, self.extra]
        self.HAMMER_EXTRA_ARGS = ' '.join([f"-p {conf}" for conf in self.PROJ_YMLS if conf]) + f" {self.args}"
        self.HAMMER_D_MK = os.getenv('HAMMER_D_MK', f"{self.OBJ_DIR}/hammer.d")

        #if __name__ == '__main__':
        # Adds configuration to system arguments, so they are visible to ArgumentParser
        HAMMER_EXTRA_ARGS_split = self.HAMMER_EXTRA_ARGS.split()
        
        #sys.argv.append("build")
        
        #for arg in ['--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
        airflow_command = sys.argv[1]
        sys.argv = []
        #for arg in [airflow_command, '--action', self.makecmdgoals, '--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
        for arg in [airflow_command, self.makecmdgoals, '--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
            sys.argv.append(arg)
        for arg in HAMMER_EXTRA_ARGS_split:
            sys.argv.append(arg)
## Current status - Determine how to fix task dependency issues
## Try function mapping or dynamic conditional dependency checks

'''
if task_function:
        # Call the corresponding function
        task_function(flow)
    else:
        raise ValueError(f"Invalid command: {flow.makecmdgoals}")
'''

@task
def build(flow):
    # Set up sys.argv with all necessary arguments
    sys.argv = [
        'hammer-vlsi',  # Command name
        'build',        # Action
        '--obj_dir', flow.OBJ_DIR,
        '-e', flow.ENV_YML
    ]
    # Add all project configs
    for conf in flow.PROJ_YMLS:
        if conf:
            sys.argv.extend(['-p', conf])
    
    # Add any additional arguments
    if flow.args:
        sys.argv.extend(flow.args.split())
    
    CLIDriver().main()

@task
def sim_rtl(flow):
    # Set up sys.argv with all necessary arguments
    sys.argv = [
        'hammer-vlsi',  # Command name
        'sim',          # Use 'sim' instead of 'sim-rtl' as it's the valid Hammer action
        '--obj_dir', flow.OBJ_DIR,
        '-e', flow.ENV_YML
    ]
    # Add all project configs
    for conf in flow.PROJ_YMLS:
        if conf:
            sys.argv.extend(['-p', conf])
    
    if flow.args:
        sys.argv.extend(flow.args.split())
    
    CLIDriver().main()

@task
def syn(flow):
    sys.argv = [
        'hammer-vlsi',
        'syn',
        '--obj_dir', flow.OBJ_DIR,
        '-e', flow.ENV_YML
    ]
    # Add all project configs
    for conf in flow.PROJ_YMLS:
        if conf:
            sys.argv.extend(['-p', conf])
    
    if flow.args:
        sys.argv.extend(flow.args.split())
    
    CLIDriver().main()

@task
def clean(flow):
    #pdb.set_trace()
    if os.path.exists(flow.OBJ_DIR):
        subprocess.run(f"rm -rf {flow.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)

#@task
#def run(self):
#    if 'clean' in sys.argv:
#        self.clean()
#    else:
#        self.build()
@task.branch
def run(flow):
    # Map actions to their corresponding tasks
    action_map = {
        "build": "build",
        "clean": "clean",
        "sim_rtl": "sim_rtl",
        "syn": "syn",
        "par": "par"
    }
    return action_map.get(flow.makecmdgoals, "sim_rtl")

@task
def par(flow):
    # Get par-input.json path from OBJ_DIR
    par_input_json = f"{flow.OBJ_DIR}/par-input.json"
    
    # Generate par-input.json if it doesn't exist
    if not os.path.exists(par_input_json):
        syn_to_par(flow)
    
    sys.argv = [
        'hammer-vlsi',
        'par',
        '--obj_dir', flow.OBJ_DIR,
        '-e', flow.ENV_YML,
        '-p', par_input_json
    ]
    
    # Add all project configs
    for conf in flow.PROJ_YMLS:
        if conf:
            sys.argv.extend(['-p', conf])
    
    if flow.args:
        sys.argv.extend(flow.args.split())
    
    CLIDriver().main()

def syn_to_par(flow):
    """
    Generate par-input.json from synthesis outputs if it doesn't exist
    """
    par_input_json = f"{flow.OBJ_DIR}/par-input.json"
    
    # Only generate if file doesn't exist
    if not os.path.exists(par_input_json):
        # Basic PAR configuration
        par_config = {
            "vlsi.inputs.placement_constraints": [],
            "vlsi.inputs.gds_merge": True,
            "par.inputs": {
                "top_module": flow.design,
                "input_files": [f"{flow.OBJ_DIR}/syn-rundir/{flow.design}.mapped.v"]
            }
        }
        
        # Write configuration to par-input.json
        with open(par_input_json, 'w') as f:
            json.dump(par_config, f, indent=2)

'''
function_map = {
    "build": build,
    "clean": clean
}
'''

@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='build'
)
def build_dag():
    # Force sim-rtl for testing
    os.environ['MAKECMDGOALS'] = 'build'
    
    flow = AIRFlow()
    import_task = import_task_to_dag()
    run_task = run(flow)
    build_task = build(flow)
    clean_task = clean(flow)
    sim_rtl_task = sim_rtl(flow)
    syn_task = syn(flow)
    par_task = par(flow)
    # Set up task dependencies
    chain(
        import_task,
        run_task,
        [build_task, clean_task, sim_rtl_task, syn_task, par_task]
    )



@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='sim-rtl'
)
def sim_rtl_dag():
    # Force sim-rtl for testing
    os.environ['MAKECMDGOALS'] = 'sim-rtl'
    
    flow = AIRFlow()
    import_task = import_task_to_dag()
    run_task = run(flow)
    build_task = build(flow)
    clean_task = clean(flow)
    sim_rtl_task = sim_rtl(flow)
    syn_task = syn(flow)
    par_task = par(flow)
    # Set up task dependencies
    chain(
        import_task,
        run_task,
        [build_task, clean_task, sim_rtl_task, syn_task, par_task]
    )

@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='syn'
)
def syn_dag():
    # Force sim-rtl for testing
    os.environ['MAKECMDGOALS'] = 'syn'
    
    flow = AIRFlow()
    import_task = import_task_to_dag()
    run_task = run(flow)
    build_task = build(flow)
    clean_task = clean(flow)
    sim_rtl_task = sim_rtl(flow)
    syn_task = syn(flow)
    par_task = par(flow)
    
    # Set up task dependencies
    chain(
        import_task,
        run_task,
        [build_task, clean_task, sim_rtl_task, syn_task, par_task]
    )

@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='par'
)
def par_dag():
    # Force sim-rtl for testing
    os.environ['MAKECMDGOALS'] = 'par'
    
    flow = AIRFlow()
    import_task = import_task_to_dag()
    run_task = run(flow)
    build_task = build(flow)
    clean_task = clean(flow)
    sim_rtl_task = sim_rtl(flow)
    syn_task = syn(flow)
    par_task = par(flow)
    # Set up task dependencies
    chain(
        import_task,
        run_task,
        [build_task, clean_task, sim_rtl_task, syn_task, par_task]
    )
#Create instance of DAG
dag = build_dag()
dag2 = sim_rtl_dag()
dag3 = syn_dag()
dag4 = par_dag()
#dag.test()

def main():
    CLIDriver().main()