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

# Define the configuration UI parameters
default_args = {
    'owner': 'airflow',
    'params': {
        'clean': {
            'type': 'boolean',
            'default': False,
            'description': 'Clean build directory'
        },
        'build': {
            'type': 'boolean',
            'default': False,
            'description': 'Run build step'
        },
        'sim_rtl': {
            'type': 'boolean',
            'default': False,
            'description': 'Run RTL simulation'
        },
        'syn': {
            'type': 'boolean',
            'default': False,
            'description': 'Run synthesis'
        },
        'par': {
            'type': 'boolean',
            'default': False,
            'description': 'Run place and route'
        }
    }
}

@dag(
    dag_id='hammer_vlsi_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
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
def create_hammer_dag():
    @task
    def clean_task(**context):
        """Clean the build directory"""
        print("Starting clean task")
        if context['dag_run'].conf.get('clean', False):
            print("Clean parameter is True, executing clean")
            flow = AIRFlow()
            import shutil
            if os.path.exists(flow.OBJ_DIR):
                shutil.rmtree(flow.OBJ_DIR)
                print(f"Cleaned directory: {flow.OBJ_DIR}")
        else:
            print("Clean parameter is False, skipping")
            raise AirflowSkipException("Clean task skipped")

    @task
    def build_task(**context):
        """Execute build task"""
        print("Starting build task")
        if context['dag_run'].conf.get('build', False):
            print("Build parameter is True, executing build")
            flow = AIRFlow()
            flow.build()
        else:
            print("Build parameter is False, skipping")
            raise AirflowSkipException("Build task skipped")

    @task
    def sim_rtl_task(**context):
        """Execute RTL simulation task"""
        print("Starting sim_rtl task")
        if context['dag_run'].conf.get('sim_rtl', False):
            print("Sim-RTL parameter is True, executing sim_rtl")
            flow = AIRFlow()
            flow.sim_rtl()
        else:
            print("Sim-RTL parameter is False, skipping")
            raise AirflowSkipException("Sim-RTL task skipped")

    @task
    def syn_task(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if context['dag_run'].conf.get('syn', False):
            print("Synthesis parameter is True, executing syn")
            flow = AIRFlow()
            flow.syn()
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def par_task(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = AIRFlow()
            flow.par()
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def clean_decider(**context):
        """Decide whether to run clean"""
        if context['dag_run'].conf.get('clean', False):
            return ['clean_task', 'build_decider']
        return 'build_decider'

    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def build_decider(**context):
        """Decide whether to run build"""
        if context['dag_run'].conf.get('build', False):
            return ['build_task', 'sim_rtl_decider']
        return 'sim_rtl_decider'

    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def sim_rtl_decider(**context):
        """Decide whether to run sim_rtl"""
        if context['dag_run'].conf.get('sim_rtl', False):
            return ['sim_rtl_task', 'syn_decider']
        return 'syn_decider'

    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_decider(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return ['syn_task', 'par_decider']
        return 'par_decider'

    @task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    def par_decider(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'par_task'
        return None

    # Create task instances
    clean_decide = clean_decider()
    clean = clean_task()
    build_decide = build_decider()
    build = build_task()
    sim_rtl_decide = sim_rtl_decider()
    sim_rtl = sim_rtl_task()
    syn_decide = syn_decider()
    syn = syn_task()
    par_decide = par_decider()
    par = par_task()

    # Set up dependencies to ensure deciders always run
    clean_decide >> [clean, build_decide]
    clean >> build_decide
    
    build_decide >> [build, sim_rtl_decide]
    build >> sim_rtl_decide
    
    sim_rtl_decide >> [sim_rtl, syn_decide]
    sim_rtl >> syn_decide
    
    syn_decide >> [syn, par_decide]
    syn >> par_decide
    
    par_decide >> par

    return {
        'clean_decide': clean_decide,
        'clean': clean,
        'build_decide': build_decide,
        'build': build,
        'sim_rtl_decide': sim_rtl_decide,
        'sim_rtl': sim_rtl,
        'syn_decide': syn_decide,
        'syn': syn,
        'par_decide': par_decide,
        'par': par
    }

# Create the DAG
hammer_dag = create_hammer_dag()

def main():
    CLIDriver().main()