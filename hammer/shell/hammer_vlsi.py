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
from airflow.models.param import Param
from airflow.utils.trigger_rule import TriggerRule
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

@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='hammer_pipeline_dag',
    params={
        'clean': Param(
            default=False,
            type='boolean',
            title='Clean Build Directory',
            description='Clean the build directory before running'
        ),
        'build': Param(
            default=False,
            type='boolean',
            title='Build Design',
            description='Run the build step'
        ),
        'sim_rtl': Param(
            default=False,
            type='boolean',
            title='RTL Simulation',
            description='Run RTL simulation'
        ),
        'syn': Param(
            default=False,
            type='boolean',
            title='Synthesis',
            description='Run logic synthesis'
        ),
        'par': Param(
            default=False,
            type='boolean',
            title='Place and Route',
            description='Run place and route'
        )
    },
    render_template_as_native_obj=True
)
def hammer_pipeline_dag():
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def start_task(**context):
        """Start task"""
        if context['dag_run'].conf.get('clean', True):
            return "clean"
        elif (context['dag_run'].conf.get('build', True) or 
            context['dag_run'].conf.get('sim_rtl', True) or
            context['dag_run'].conf.get('syn', True) or
            context['dag_run'].conf.get('par', True)):
            return "build_decide"
        else:
            return "exit_task"
    
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def build_decide(**context):
        """Decide whether to run build"""  
        if context['dag_run'].conf.get('build', True):
            return "build"
        elif (context['dag_run'].conf.get('sim_rtl', True) or
            context['dag_run'].conf.get('syn', True) or
            context['dag_run'].conf.get('par', True)):
            return "sim_or_syn_decide"
        else:
            return "exit_task"

    @task.branch(trigger_rule=TriggerRule.ONE_SUCCESS)  
    def sim_or_syn_decide(**context):
        """Decide whether to run sim_rtl or syn"""
        if context['dag_run'].conf.get('sim_rtl', True):
            return "sim_rtl"
        else:
            return "syn_decide"

    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decide(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', True):
            return "syn"
        elif (context['dag_run'].conf.get('par', True)):
            return "par_decide"
        else:
            return "exit_task"

    @task.branch(trigger_rule=TriggerRule.ONE_SUCCESS)
    def par_decide(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', True):
            return 'par'
        else:
            return "exit_task"

    @task(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def exit_task():
        """Exit task"""
        print("Exiting")

    ##Airflow branches
    start = start_task()
    build_choice = build_decide()
    sim_or_syn_choice = sim_or_syn_decide()
    syn_choice = syn_decide()
    par_choice = par_decide()
    finish = exit_task()
    ##Hammer task from airflow class
    flow = AIRFlow()
    clean_task = clean(flow)
    build_task = build(flow)
    sim_rtl_task = sim_rtl(flow)
    syn_task = syn(flow)
    par_task = par(flow)
    # Set up task dependencies
    start >> [clean_task, build_choice, finish]
    clean_task >> finish
    build_choice >> [build_task, sim_or_syn_choice, finish]
    build_task >> sim_or_syn_choice >> [sim_rtl_task, syn_choice]
    sim_rtl_task >> finish 
    syn_choice >> [syn_task, par_choice, finish]
    syn_task >> par_choice >> [par_task, finish]
    par_task >> finish

#Create instance of DAG
dag = hammer_pipeline_dag()

def main():
    CLIDriver().main()
