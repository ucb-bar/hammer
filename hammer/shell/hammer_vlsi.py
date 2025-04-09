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

import pendulum

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




@dag(
    dag_id='Sledgehammer_demo_gcd',
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Los_Angeles"),
    schedule=None,
    catchup=False,
    tags=["gcd"],
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
def create_hammer_dag_gcd():
    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def start(**context):
        """Start task"""
        if context['dag_run'].conf.get('clean', False):
            return "clean"
        elif (context['dag_run'].conf.get('build', False) or 
            context['dag_run'].conf.get('sim_rtl', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "build_decider"
        else:
            return "exit_"

    @task
    def clean(**context):
        """Clean the build directory"""
        print("Starting clean task")
        flow = AIRFlow()
        if os.path.exists(flow.OBJ_DIR):
            subprocess.run(f"rm -rf {flow.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)
    
    @task
    def build(**context):
        """Execute build task"""
        print("Starting build task")
        if context['dag_run'].conf.get('build', False):
            print("Build parameter is True, executing build")
            flow = AIRFlow()
            flow.build()
        else:
            print("Build parameter is False, skipping")
            raise AirflowSkipException("Build task skipped")

    #Bug where sim_or_syn_decide is being triggered, even when clean is passed in.
    #Cannot use ONE_SUCCESS bc of start
    #Cannot use NONE_FAILED bc of clean
    #Cannot use ALL_SUCCESS bc of build
    #Cannot use NONE_SKIPPED bc of build
    #Need to either find trigger flag to pass in, so this task runs if build_decider is success or change flow graph
    #@task
    #@task.branch(trigger_rule=TriggerRule.ONE_SUCCESS)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def sim_or_syn_decide(**context):
        """Decide whether to run sim_rtl or syn"""
        if context['dag_run'].conf.get('sim_rtl', False):
            return 'sim_rtl'
        elif (context['dag_run'].conf.get('syn', False) or 
            context['dag_run'].conf.get('par', False)):
            return 'syn_decider'
        return 'exit_'

    @task
    def sim_rtl(**context):
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
    def syn(**context):
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
    def par(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = AIRFlow()
            flow.par()
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def build_decider(**context):
        """Decide whether to run build"""
        if context['dag_run'].conf.get('build', True):
            return 'build'
        elif (context['dag_run'].conf.get('sim_rtl', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "sim_or_syn_decide"
        return 'exit_'

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'syn'
        elif (context['dag_run'].conf.get('par', False)):
            return "par_decider"
        else:
            return "exit_"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'par'
        return 'exit_'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_():
        """Exit task"""
        print("Exiting")
        sys.exit(0)

    # Create task instances
    start = start()
    clean = clean()
    build_decide = build_decider()
    build = build()
    sim_or_syn_decide = sim_or_syn_decide()
    sim_rtl = sim_rtl()
    syn_decide = syn_decider()
    syn = syn()
    par_decide = par_decider()
    par = par()
    exit_ = exit_()

    # Set up dependencies to ensure deciders always run
    start >> [clean, build_decide, exit_]
    clean >> exit_
    build_decide >> [build, sim_or_syn_decide, exit_]
    build >> sim_or_syn_decide
    sim_or_syn_decide >> [sim_rtl, syn_decide, exit_]
    sim_rtl >> exit_
    syn_decide >> [syn, par_decide, exit_]
    syn >> par_decide
    par_decide >> [par, exit_]
    par >> exit_

    return {
        'clean': clean,
        'build_decide': build_decide,
        'build': build,
        'sim_or_syn_decide': sim_or_syn_decide,
        'sim_rtl': sim_rtl,
        'syn_decide': syn_decide,
        'syn': syn,
        'par_decide': par_decide,
        'par': par
    }

# Create the DAG
hammer_dag_gcd = create_hammer_dag_gcd()

class AIRFlow_rocket:
    def __init__(self):
        # minimal flow configuration variables
        self.design = os.getenv('design', 'intel2x2')
        self.pdk = os.getenv('pdk', 'intech22')
        self.tools = os.getenv('tools', 'cm')
        self.env = os.getenv('env', 'intel2x2')
        self.extra = os.getenv('extra', '')  # extra configs
        self.args = os.getenv('args', '')  # command-line args (including step flow control)
        
        # Directory structure
        self.vlsi_dir = os.path.abspath('../e2e/')
        self.specs_abs = os.path.abspath('../../specs')
        self.e2e_dir = os.getenv('e2e_dir', self.vlsi_dir)
        self.specs_dir = os.getenv('specs_dir', self.specs_abs) #Point to specs directory for intel2x2 yml files
        self.OBJ_DIR = os.getenv('OBJ_DIR', f"{self.e2e_dir}/build-{self.pdk}-{self.tools}/{self.design}")
        
        # non-overlapping default configs
        self.ENV_YML = os.getenv('ENV_YML', f"{self.specs_dir}/{self.env}-env.yml") #Point to intel2x2-env.yml
        self.PDK_CONF = os.getenv('PDK_CONF', f"{self.specs_dir}/{self.env}-tech.yml") #Kind of confusing, but the pdk yml file is named intel2x2 instead of intech22
        self.TOOLS_CONF = os.getenv('TOOLS_CONF', f"{self.e2e_dir}/configs-tool/{self.tools}.yml") #Can keep the same for genus/innovus

        # design-specific overrides of default configs
        self.DESIGN_CONF = os.getenv('DESIGN_CONF', f"{self.specs_dir}/{self.design}-design-common.yml") #Point to intel2x2-design-common.yml
        self.DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"{self.specs_dir}/rockettile-design.yml") #Point to rockettile-design.yml, which contains same info as syn.yml (intel2x2)
        
        # synthesis and par configurations
        #self.SYN_CONF = os.getenv('SYN_CONF', f"{self.specs_dir}/rockettile-design.yml") #Point to rockettile-design.yml, which contains same info as syn.yml (intel2x2)
        #self.PAR_CONF = os.getenv('PAR_CONF', f"{self.e2e_dir}/configs-design/{self.design}/par.yml")
        
        # This should be your target, build is passed in
        
        #self.makecmdgoals = os.getenv('MAKECMDGOALS', "build")
        
        ## simulation and power configurations
        #self.SIM_CONF = os.getenv('SIM_CONF',
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-rtl.yml" if '-rtl' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-syn.yml" if '-syn' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-par.yml" if '-par' in self.makecmdgoals else ''
        #)
        #self.POWER_CONF = os.getenv('POWER_CONF',
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-rtl-{self.pdk}.yml" if 'power-rtl' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-syn-{self.pdk}.yml" if 'power-syn' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-par-{self.pdk}.yml" if 'power-par' in self.makecmdgoals else ''
        #)
        
        # create project configuration
        self.PROJ_YMLS = [
            self.PDK_CONF, 
            self.TOOLS_CONF, 
            self.DESIGN_CONF, 
            self.DESIGN_PDK_CONF,
            #self.SYN_CONF, 
            #self.SIM_CONF, 
            #self.POWER_CONF, 
            self.extra
        ]
        
        self.HAMMER_EXTRA_ARGS = ' '.join([f"-p {conf}" for conf in self.PROJ_YMLS if conf]) + f" {self.args}"
        self.HAMMER_D_MK = os.getenv('HAMMER_D_MK', f"{self.OBJ_DIR}/hammer.d")

        # Set up system arguments
        
        #airflow_command = sys.argv[1]
        #sys.argv = []
        #for arg in [airflow_command, self.makecmdgoals, '--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
        #    sys.argv.append(arg)
        #for arg in self.HAMMER_EXTRA_ARGS.split():
        #    sys.argv.append(arg)

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
        self.SIM_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
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
        self.SYN_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
        self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.json
        print(f"SYN_CONF: {self.SYN_CONF}")
        print(f"SRAM_CONF: {self.SRAM_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            'syn-RocketTile',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            '-p', self.SYN_CONF,
            '-p', self.SRAM_CONF
        ]
        
        if self.extra:
            sys.argv.extend(['-p', self.extra])
        
        if self.args:
            sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def sram_generator(self):
        print("Executing sram_generator")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        print(f"PDK_CONF: {self.PDK_CONF}")
        print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
    
        # Add synthesis config
        self.SYN_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
        self.SRAM_GENERATOR_CONF = (f"{self.OBJ_DIR}/sram_generator-input.yml") #Point to sram_generator-input.yml
        self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.json
        
        print(f"SYN_CONF: {self.SYN_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            'sram_generator',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            '-p', self.SYN_CONF,
            '-p', self.SRAM_GENERATOR_CONF
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
        #par_input_json = f"{self.OBJ_DIR}/par-input.json"
        par_input_json = f"{self.OBJ_DIR}/par-RocketTile-input.json"
        
        print("Executing syn-to-par")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        print(f"PDK_CONF: {self.PDK_CONF}")
        print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
    
        # Add synthesis config
        self.SYN_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
        #self.SRAM_GENERATOR_CONF = (f"{self.OBJ_DIR}/sram_generator-input.yml") #Point to sram_generator-input.yml
        #self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.json
        
        print(f"SYN_CONF: {self.SYN_CONF}")
        #par_input_json = "/bwrcq/C/andre_green/chipyard-sledgehammer/vlsi/hammer/e2e/build-intech22-cm/intel2x2/par-RocketTile-input.json"
        syn_output = f"{self.OBJ_DIR}/syn-RocketTile/syn-output-full.json"
        #syn_output = "/bwrcq/C/andre_green/chipyard-sledgehammer/vlsi/hammer/e2e/build-intech22-cm/intel2x2/syn-RocketTile/syn-output-full.json"
        
        sys.argv = [
            'hammer-vlsi',
            'syn-to-par',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            '-p', self.SYN_CONF,
            #'-p', self.SRAM_GENERATOR_CONF,
            '-p', syn_output,
            '-o', par_input_json
        ]
        
        if self.extra:
            sys.argv.extend(['-p', self.extra])
        
        if self.args:
            sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()
        
        
        '''
        # Only generate if file doesn't exist
        if not os.path.exists(par_input_json):
            print("Generating par-input.json")
            par_config = {
                "vlsi.inputs.placement_constraints": [],
                "vlsi.inputs.gds_merge": True,
                "par.inputs": {
                    #"top_module": self.design,
                    "top_module": "RocketTile",
                    "input_files": [f"{self.OBJ_DIR}/syn-rundir/RocketTile.mapped.v"]
                }
            }
            
            # Write configuration to par-input.json
            with open(par_input_json, 'w') as f:
                json.dump(par_config, f, indent=2)
        '''        
        return par_input_json

    def par(self):
        """Execute PAR flow."""
        # Generate par-input.json
        #par_input_json = self.syn_to_par()

        #self.PAR_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
        par_input_json = f"{self.OBJ_DIR}/par-RocketTile-input.json"
        
        # Set up command line arguments
        sys.argv = [
            'hammer-vlsi',
            'par-RocketTile',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.PDK_CONF,
            '-p', self.TOOLS_CONF,
            '-p', self.DESIGN_CONF,
            '-p', self.DESIGN_PDK_CONF,
            #'-p', self.PAR_CONF,
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




@dag(
    dag_id='Sledgehammer_demo_rocket',
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Los_Angeles"),
    schedule=None,
    catchup=False,
    tags=["rocket"],
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
        'sram_generator': Param(
            default=False,
            type='boolean',
            title='SRAM Generator',
            description='Generate SRAM macros'
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
def create_hammer_dag_rocket():
    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def start(**context):
        """Start task"""
        if context['dag_run'].conf.get('clean', False):
            return "clean"
        elif (context['dag_run'].conf.get('build', False) or 
            context['dag_run'].conf.get('sim_rtl', False) or
            context['dag_run'].conf.get('sram_generator', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "build_decider"
        else:
            return "exit_"

    @task
    def clean(**context):
        """Clean the build directory"""
        print("Starting clean task")
        flow = AIRFlow_rocket()
        if os.path.exists(flow.OBJ_DIR):
            subprocess.run(f"rm -rf {flow.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)
    
    @task
    def build(**context):
        """Execute build task"""
        print("Starting build task")
        if context['dag_run'].conf.get('build', False):
            print("Build parameter is True, executing build")
            flow = AIRFlow_rocket()
            flow.build()
        else:
            print("Build parameter is False, skipping")
            raise AirflowSkipException("Build task skipped")

    #Bug where sim_or_syn_decide is being triggered, even when clean is passed in.
    #Cannot use ONE_SUCCESS bc of start
    #Cannot use NONE_FAILED bc of clean
    #Cannot use ALL_SUCCESS bc of build
    #Cannot use NONE_SKIPPED bc of build
    #Need to either find trigger flag to pass in, so this task runs if build_decider is success or change flow graph
    #@task
    #@task.branch(trigger_rule=TriggerRule.ONE_SUCCESS)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def sim_or_syn_decide(**context):
        """Decide whether to run sim_rtl or syn"""
        if context['dag_run'].conf.get('sim_rtl', False):
            return 'sim_rtl'
        elif (context['dag_run'].conf.get('sram_generator', False) or 
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return 'syn_decider'
        return 'exit_'

    @task
    def sim_rtl(**context):
        """Execute RTL simulation task"""
        print("Starting sim_rtl task")
        if context['dag_run'].conf.get('sim_rtl', False):
            print("Sim-RTL parameter is True, executing sim_rtl")
            flow = AIRFlow_rocket()
            flow.sim_rtl()
        else:
            print("Sim-RTL parameter is False, skipping")
            raise AirflowSkipException("Sim-RTL task skipped")

    @task
    def sram_generator(**context):
        """Execute sram generator task"""
        print("Starting sram task")
        if context['dag_run'].conf.get('sram_generator', False):
            print("SRAM parameter is True, executing sram_generator")
            flow = AIRFlow_rocket()
            flow.sram_generator()
        else:
            print("SRAM parameter is False, skipping")
            raise AirflowSkipException("SRAM task skipped")

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = AIRFlow_rocket()
            flow.syn()
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = AIRFlow_rocket()
            flow.syn_to_par()
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = AIRFlow_rocket()
            flow.par()
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def build_decider(**context):
        """Decide whether to run build"""
        if context['dag_run'].conf.get('build', True):
            return 'build'
        elif (context['dag_run'].conf.get('sim_rtl', False) or
            context['dag_run'].conf.get('sram_generator', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "sim_or_syn_decide"
        return 'exit_'

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('sram_generator', False):
            return 'sram_generator'
        elif context['dag_run'].conf.get('syn', False):
            return 'syn'
        elif (context['dag_run'].conf.get('par', False)):
            return "par_decider"
        else:
            return "exit_"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'syn_to_par'
        return 'exit_'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_():
        """Exit task"""
        print("Exiting")
        sys.exit(0)

    # Create task instances
    start = start()
    clean = clean()
    build_decide = build_decider()
    build = build()
    sim_or_syn_decide = sim_or_syn_decide()
    sim_rtl = sim_rtl()
    syn_decide = syn_decider()
    sram_generator = sram_generator()
    syn = syn()
    par_decide = par_decider()
    syn_to_par = syn_to_par()
    par = par()
    exit_ = exit_()

    # Set up dependencies to ensure deciders always run
    start >> [clean, build_decide, exit_]
    clean >> exit_
    build_decide >> [build, sim_or_syn_decide, exit_]
    build >> sim_or_syn_decide
    sim_or_syn_decide >> [sim_rtl, syn_decide, exit_]
    sim_rtl >> exit_
    syn_decide >> [syn, sram_generator, par_decide, exit_]
    sram_generator >> syn
    syn >> par_decide
    par_decide >> [syn_to_par, exit_]
    syn_to_par >> par
    par >> exit_

    return {
        'clean': clean,
        'build_decide': build_decide,
        'build': build,
        'sim_or_syn_decide': sim_or_syn_decide,
        'sim_rtl': sim_rtl,
        'syn_decide': syn_decide,
        'sram_generator': sram_generator,
        'syn': syn,
        'par_decide': par_decide,
        'syn_to_par': syn_to_par,
        'par': par
    }

# Create the DAG
hammer_dag_rocket = create_hammer_dag_rocket()


def main():
    CLIDriver().main()