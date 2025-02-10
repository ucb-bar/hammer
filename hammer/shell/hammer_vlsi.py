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
from airflow.models.param import Param
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime
from airflow.exceptions import AirflowSkipException
from airflow.decorators import task, dag
from airflow.models import Variable

# Add the parent directory to the Python path to allow imports from 'vlsi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vlsi')))

from hammer.vlsi import CLIDriver
from hammer.vlsi.cli_driver import import_task_to_dag
#import pdb
#pdb.set_trace()
class AIRFlow:
    def __init__(self):
        # minimal flow configuration variables
        self.design = os.getenv('design', 'gcd')
        self.pdk = os.getenv('pdk', 'sky130')
        self.tools = os.getenv('tools', 'cm')
        self.env = os.getenv('env', 'bwrc')
        self.extra = os.getenv('extra', '')  # extra configs
        self.args = os.getenv('args', '')  # command-line args (including step flow control)
        
        # Directory structure
        self.vlsi_dir = os.path.abspath('../e2e/')
        self.e2e_dir = os.getenv('e2e_dir', self.vlsi_dir)
        self.OBJ_DIR = os.getenv('OBJ_DIR', f"{self.e2e_dir}/build-{self.pdk}-{self.tools}/{self.design}")
        
        # non-overlapping default configs
        self.ENV_YML = os.getenv('ENV_YML', f"{self.e2e_dir}/configs-env/{self.env}-env.yml")
        self.PDK_CONF = os.getenv('PDK_CONF', f"{self.e2e_dir}/configs-pdk/{self.pdk}.yml")
        self.TOOLS_CONF = os.getenv('TOOLS_CONF', f"{self.e2e_dir}/configs-tool/{self.tools}.yml")

        # design-specific overrides of default configs
        self.DESIGN_CONF = os.getenv('DESIGN_CONF', f"{self.e2e_dir}/configs-design/{self.design}/common.yml")
        self.DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"{self.e2e_dir}/configs-design/{self.design}/{self.pdk}.yml")
        
        # synthesis and par configurations
        self.SYN_CONF = os.getenv('SYN_CONF', f"{self.e2e_dir}/configs-design/{self.design}/syn.yml")
        self.PAR_CONF = os.getenv('PAR_CONF', f"{self.e2e_dir}/configs-design/{self.design}/par.yml")
        
        # This should be your target, build is passed in
        self.makecmdgoals = os.getenv('MAKECMDGOALS', "build")
        
        # simulation and power configurations
        self.SIM_CONF = os.getenv('SIM_CONF',
            f"{self.e2e_dir}/configs-design/{self.design}/sim-rtl.yml" if '-rtl' in self.makecmdgoals else
            f"{self.e2e_dir}/configs-design/{self.design}/sim-syn.yml" if '-syn' in self.makecmdgoals else
            f"{self.e2e_dir}/configs-design/{self.design}/sim-par.yml" if '-par' in self.makecmdgoals else ''
        )
        self.POWER_CONF = os.getenv('POWER_CONF',
            f"{self.e2e_dir}/configs-design/{self.design}/power-rtl-{self.pdk}.yml" if 'power-rtl' in self.makecmdgoals else
            f"{self.e2e_dir}/configs-design/{self.design}/power-syn-{self.pdk}.yml" if 'power-syn' in self.makecmdgoals else
            f"{self.e2e_dir}/configs-design/{self.design}/power-par-{self.pdk}.yml" if 'power-par' in self.makecmdgoals else ''
        )

        # create project configuration
        self.PROJ_YMLS = [
            self.PDK_CONF, 
            self.TOOLS_CONF, 
            self.DESIGN_CONF, 
            self.DESIGN_PDK_CONF,
            self.SYN_CONF, 
            self.SIM_CONF, 
            self.POWER_CONF, 
            self.extra
        ]
        
        self.HAMMER_EXTRA_ARGS = ' '.join([f"-p {conf}" for conf in self.PROJ_YMLS if conf]) + f" {self.args}"
        self.HAMMER_D_MK = os.getenv('HAMMER_D_MK', f"{self.OBJ_DIR}/hammer.d")

        # Set up system arguments
        airflow_command = sys.argv[1]
        sys.argv = []
        for arg in [airflow_command, self.makecmdgoals, '--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
            sys.argv.append(arg)
        for arg in self.HAMMER_EXTRA_ARGS.split():
            sys.argv.append(arg)

    def build(self):
        print("Executing build")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        print(f"PDK_CONF: {self.PDK_CONF}")
        print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            'build',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF
        ]
        
        if self.extra:
            sys.argv.extend(['-p', self.extra])
        
        if self.args:
            sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def sim_rtl(self):
        print("Executing sim-rtl")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        print(f"PDK_CONF: {self.PDK_CONF}")
        print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
        
        # Add simulation config
        self.SIM_CONF = os.path.join(self.e2e_dir, "configs-design", self.design, "sim-rtl.yml")
        print(f"SIM_CONF: {self.SIM_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            'sim',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            '-p', self.SIM_CONF
        ]
        
        if self.extra:
            sys.argv.extend(['-p', self.extra])
        
        if self.args:
            sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def syn(self):
        print("Executing synthesis")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        print(f"PDK_CONF: {self.PDK_CONF}")
        print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
        
        # Add synthesis config
        self.SYN_CONF = os.path.join(self.e2e_dir, "configs-design", self.design, "syn.yml")
        print(f"SYN_CONF: {self.SYN_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            'syn',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            '-p', self.SYN_CONF
        ]
        
        if self.extra:
            sys.argv.extend(['-p', self.extra])
        
        if self.args:
            sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def syn_to_par(self):
        """
        Generate par-input.json from synthesis outputs if it doesn't exist
        """
        par_input_json = f"{self.OBJ_DIR}/par-input.json"
        
        # Only generate if file doesn't exist
        if not os.path.exists(par_input_json):
            print("Generating par-input.json")
            par_config = {
                "vlsi.inputs.placement_constraints": [],
                "vlsi.inputs.gds_merge": True,
                "par.inputs": {
                    "top_module": self.design,
                    "input_files": [f"{self.OBJ_DIR}/syn-rundir/{self.design}.mapped.v"]
                }
            }
            
            # Write configuration to par-input.json
            with open(par_input_json, 'w') as f:
                json.dump(par_config, f, indent=2)
        
        return par_input_json

    def par(self):
        """Execute PAR flow."""
        # Generate par-input.json
        par_input_json = self.syn_to_par()

        # Set up command line arguments
        sys.argv = [
            'hammer-vlsi',
            'par',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', par_input_json
        ]
        
        # Add all project configs
        for conf in self.PROJ_YMLS:
            if conf:
                sys.argv.extend(['-p', conf])
        
        if self.args:
            sys.argv.extend(self.args.split())
        
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def clean(self):
        print("Executing clean")
        if os.path.exists(self.OBJ_DIR):
            subprocess.run(f"rm -rf {self.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)

def generic_task_callable(task_name, flow):
    """
    Generic callable for handling different hammer tasks.
    Args:
        task_name: Name of the task to execute (e.g., 'build_task', 'sim_rtl_task')
        flow: AIRFlow instance containing configuration
    """
    # Map UI task names to hammer commands
    task_map = {
        'build_task': 'build',
        'sim_rtl_task': 'sim',
        'syn_task': 'syn',
        'par_task': 'par',
        'clean_task': 'clean'
    }
    
    if task_name not in task_map:
        raise ValueError(f"Unknown task: {task_name}. Available tasks: {list(task_map.keys())}")
    
    hammer_action = task_map[task_name]
    
    # Set up sys.argv with common arguments
    sys.argv = [
        'hammer-vlsi',      # Command name
        hammer_action,      # Action
        '--obj_dir', flow.OBJ_DIR,
        '-e', flow.ENV_YML
    ]
    
    # Add all project configs
    for conf in flow.PROJ_YMLS:
        if conf and conf != '':
            sys.argv.extend(['-p', conf])
    
    # Add any additional arguments from flow
    if flow.args:
        sys.argv.extend(flow.args.split())
    
    print(f"Running hammer-vlsi with arguments: {sys.argv}")
    
    try:
        CLIDriver().main()
    except Exception as e:
        print(f"Error executing {task_name}: {str(e)}")
        raise

@task.branch(task_id='start_task')
def start_task(**context):
    """Initial branching task"""
    tasks_to_run = []
    if context['dag_run'].conf.get('clean', False):
        tasks_to_run.append('clean_task')
    tasks_to_run.append('build_decision')
    tasks_to_run.append('exit_task')
    return tasks_to_run

def build_decide(**context):
    """Decide whether to run build"""
    if context['dag_run'].conf.get('build', False):
        return ['build_task', 'sim_or_syn_decision']
    return ['sim_or_syn_decision', 'exit_task']

def sim_or_syn_decide(**context):
    """Decide whether to run sim_rtl or continue to syn"""
    if context['dag_run'].conf.get('sim_rtl', False):
        return 'sim_rtl_task'
    return 'syn_decision'

def syn_decide(**context):
    """Decide whether to run synthesis"""
    if context['dag_run'].conf.get('syn', False):
        return ['syn_task', 'par_decision']
    return ['par_decision', 'exit_task']

def par_decide(**context):
    """Decide whether to run par"""
    if context['dag_run'].conf.get('par', False):
        return 'par_task'
    return 'exit_task'

@dag(
    schedule_interval=None,
    schedule=None,
    start_date=datetime(2024, 1, 1, 0, 0),
    catchup=False,
    dag_id='hammer_vlsi'
)
def hammer_vlsi_dag():
    flow = AIRFlow()
    
    # Create tasks
    start = start_task()
    
    # Create decision tasks
    build_decision = PythonOperator(
        task_id='build_decision',
        python_callable=build_decide,
        provide_context=True
    )
    
    sim_or_syn_decision = PythonOperator(
        task_id='sim_or_syn_decision',
        python_callable=sim_or_syn_decide,
        provide_context=True
    )
    
    syn_decision = PythonOperator(
        task_id='syn_decision',
        python_callable=syn_decide,
        provide_context=True
    )
    
    par_decision = PythonOperator(
        task_id='par_decision',
        python_callable=par_decide,
        provide_context=True
    )
    
    # Create execution tasks
    clean_task = PythonOperator(
        task_id='clean_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'clean_task', 'flow': flow}
    )
    
    build_task = PythonOperator(
        task_id='build_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'build_task', 'flow': flow}
    )
    
    sim_rtl_task = PythonOperator(
        task_id='sim_rtl_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'sim_rtl_task', 'flow': flow}
    )
    
    syn_task = PythonOperator(
        task_id='syn_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'syn_task', 'flow': flow}
    )
    
    par_task = PythonOperator(
        task_id='par_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'par_task', 'flow': flow}
    )
    
    exit_task = PythonOperator(
        task_id='exit_task',
        python_callable=lambda **context: print("Path completed")
    )
    
    # Set dependencies using operators
    start.set_downstream([clean_task, build_decision, exit_task])
    clean_task.set_downstream([build_decision, exit_task])
    build_decision.set_downstream([build_task, sim_or_syn_decision, exit_task])
    build_task.set_downstream(sim_or_syn_decision)
    sim_or_syn_decision.set_downstream([sim_rtl_task, syn_decision])
    sim_rtl_task.set_downstream(exit_task)
    syn_decision.set_downstream([syn_task, par_decision, exit_task])
    syn_task.set_downstream(par_decision)
    par_decision.set_downstream([par_task, exit_task])
    par_task.set_downstream(exit_task)

# Create the DAG instance
dag = hammer_vlsi_dag()

def main():
    CLIDriver().main()