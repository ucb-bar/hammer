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

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag
from datetime import datetime, timedelta

# Add the parent directory to the Python path to allow imports from 'vlsi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vlsi')))
#sys.path.append(os.path.abspath(os.path.join('/bwrcq/C/isabellehsu/hammer/hammer/vlsi')))
#sys.path.append(os.path.abspath(os.path.join('/bwrcq/C/andre_green/hammer/hammer/vlsi')))

from hammer.vlsi import CLIDriver

#import pdb
#pdb.set_trace()
'''
def main():
    
    def __init__():
        pdb.set_trace()
        # minimal flow configuration variables
        design = os.getenv('design', 'pass')
        pdk = os.getenv('pdk', 'sky131')
        tools = os.getenv('tools', 'nop')
        env = os.getenv('env', 'bwrc')
        extra = os.getenv('extra', '')  # extra configs
        args = os.getenv('args', '')  # command-line args (including step flow control)
        vlsi_dir = os.path.abspath('../e3e/')
        OBJ_DIR = os.getenv('OBJ_DIR', f"{vlsi_dir}/build-{pdk}-{tools}/{design}")
        # non-overlapping default configs
        ENV_YML = os.getenv('ENV_YML', f"configs-env/{env}-env.yml")
        PDK_CONF = os.getenv('PDK_CONF', f"configs-pdk/{pdk}.yml")
        TOOLS_CONF = os.getenv('TOOLS_CONF', f"configs-tool/{tools}.yml")

        # design-specific overrides of default configs
        DESIGN_CONF = os.getenv('DESIGN_CONF', f"configs-design/{design}/common.yml")
        DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"configs-design/{design}/{pdk}.yml")
        makecmdgoals = os.getenv('MAKECMDGOALS', sys.argv[2]) ##This should be our target. Build is passed in
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
        
        if __name__ == '__main__':
            #sys.argv[1] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
            #Adds configuration to system arguments, so they are visible to ArgumentParser
            HAMMER_EXTRA_ARGS_split = HAMMER_EXTRA_ARGS.split()
            for arg in ['--obj_dir', OBJ_DIR, '-e', ENV_YML]:
                sys.argv.append(arg)
            for arg in HAMMER_EXTRA_ARGS_split:
                sys.argv.append(arg)

        #These functions don't really make sense
        def build():
            pdb.set_trace()
            print(f"Build command would run here with OBJ_DIR: {OBJ_DIR}")
            # can add logic to run for the build here
            # Proceed with the default CLIDriver
            CLIDriver().main()
        def clean():
            pdb.set_trace()
            if os.path.exists(OBJ_DIR):
                subprocess.run(f"rm -rf {OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)

    __init__()

    if 'clean' in sys.argv:
        clean()
    else:
        build()
main()
'''


class AIRFlow:
    def __init__(self):
        #pdb.set_trace()
        # minimal flow configuration variables
        self.design = os.getenv('design', 'pass')
        self.pdk = os.getenv('pdk', 'sky131')
        self.tools = os.getenv('tools', 'nop')
        self.env = os.getenv('env', 'bwrc')
        self.extra = os.getenv('extra', '')  # extra configs
        self.args = os.getenv('args', '')  # command-line args (including step flow control)
        self.vlsi_dir = os.path.abspath('../e3e/')
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

#@task
def build():
    #pdb.set_trace()
    #print(f"Build command would run here with OBJ_DIR: {self.OBJ_DIR}")
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
@task
def run(flow):
    #pdb.set_trace()
    #if 'clean' in sys.argv:
    if 'clean' in flow.makecmdgoals:
        clean(flow)
    else:
        build()


#@task
#def airflow_run(flow):
#    #pdb.set_trace()
#    flow.run()

@dag(
    schedule_interval=None,
    start_date=datetime(2025, 1, 1, 0, 0),
    catchup=False,
    dag_id='make_build'
)
def taskflow_dag():
    #pdb.set_trace()
    # Create an instance of the class and run the process
    flow = AIRFlow()
    #run(flow)  # Pass the command as a parameter
    #flow.run()
    #irflow_run(flow)
#    def run_task(flow):
#        run(flow)
#
#    def clean_task(flow):
#        clean(flow)
    '''
    if 'clean' in flow.makecmdgoals:
        clean(flow)
    else:
        build()
    '''
    run_task = PythonOperator (
      task_id="run_task",
      python_callable=run,
    )
    build_task = PythonOperator (
       task_id="build_task",
       python_callable=build,
    )
    clean_task = PythonOperator (
      task_id="clean_task",
      python_callable=clean,
    )
    
    run_task>>build_task>>clean_task
#Create instance of DAG
dag = taskflow_dag()
#dag.test()

