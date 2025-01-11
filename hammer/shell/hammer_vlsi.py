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

def build_task(**context):
    print("Starting build task")
    if context['dag_run'].conf.get('build', False):
        print("Build parameter is True, executing build")
        flow = AIRFlow()
        flow.build()
    else:
        print("Build parameter is False, skipping")
        raise AirflowSkipException("Build task skipped")

def sim_rtl_task(**context):
    print("Starting sim_rtl task")
    if context['dag_run'].conf.get('sim_rtl', False):
        print("Sim-RTL parameter is True, executing sim_rtl")
        flow = AIRFlow()
        flow.sim_rtl()
    else:
        print("Sim-RTL parameter is False, skipping")
        raise AirflowSkipException("Sim-RTL task skipped")

def syn_task(**context):
    print("Starting syn task")
    if context['dag_run'].conf.get('syn', False):
        print("Synthesis parameter is True, executing syn")
        flow = AIRFlow()
        flow.syn()
    else:
        print("Synthesis parameter is False, skipping")
        raise AirflowSkipException("Synthesis task skipped")

def par_task(**context):
    print("Starting par task")
    if context['dag_run'].conf.get('par', False):
        print("PAR parameter is True, executing par")
        flow = AIRFlow()      
        flow.par()
    else:
        print("PAR parameter is False, skipping")
        raise AirflowSkipException("PAR task skipped")

def clean_task(**context):
    print("Starting clean task")
    if context['dag_run'].conf.get('clean', False):
        print("Clean parameter is True, executing clean")
        flow = AIRFlow()
        flow.clean()
    else:
        print("Clean parameter is False, skipping")
        raise AirflowSkipException("Clean task skipped")

# Create the DAG
dag = DAG(
    'hammer_vlsi_pipeline',
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        'clean': Param(False, type='boolean', title='Clean'),
        'build': Param(False, type='boolean', title='Build'),
        'sim_rtl': Param(False, type='boolean', title='Simulation RTL'),
        'syn': Param(False, type='boolean', title='Synthesis'),
        'par': Param(False, type='boolean', title='Place and Route'),
    }
)

# Create tasks with no dependencies - clean first
clean_op = PythonOperator(
    task_id='clean',
    python_callable=clean_task,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

build_op = PythonOperator(
    task_id='build',
    python_callable=build_task,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

sim_rtl_op = PythonOperator(
    task_id='sim_rtl',
    python_callable=sim_rtl_task,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

syn_op = PythonOperator(
    task_id='syn',
    python_callable=syn_task,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

par_op = PythonOperator(
    task_id='par',
    python_callable=par_task,
    provide_context=True,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# No dependencies - all tasks run independently

def main():
    CLIDriver().main()