import os
import sys
import subprocess
import tempfile
import yaml
from datetime import datetime, timedelta
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from hammer.vlsi import CLIDriver

# Define the AIRFlow class
class AIRFlow:
    def __init__(self, design=None, pdk=None, tools=None, env=None, extra_args=None):
        # Get parameters from args or environment variables
        self.design = str(design or os.getenv('design', 'gcd'))
        self.pdk = str(pdk or os.getenv('pdk', 'sky130'))
        self.tools = str(tools or os.getenv('tools', 'cm'))
        self.env = str(env or os.getenv('env', 'bwrc'))
        self.extra = str(extra_args or os.getenv('extra', ''))
        self.args = str(os.getenv('args', ''))
        
        # Set up paths with shorter names
        self.vlsi_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../e2e'))
        
        # Set up paths exactly as in the backup file
        self.OBJ_DIR = f"{self.vlsi_dir}/build-{self.pdk}-{self.tools}/{self.design}"
        self.ENV_YML = f"configs-env/{self.env}-env.yml"
        self.PDK_CONF = f"configs-pdk/{self.pdk}.yml"
        self.TOOLS_CONF = f"configs-tool/{self.tools}.yml"
        self.DESIGN_CONF = f"configs-design/{self.design}/common.yml"
        self.DESIGN_PDK_CONF = f"configs-design/{self.design}/{self.pdk}.yml"
        self.PROJ_YMLS = [self.PDK_CONF, self.TOOLS_CONF, self.DESIGN_CONF, self.DESIGN_PDK_CONF]

def create_flow(**context):
    """Create AIRFlow instance from DAG parameters"""
    params = context.get('params', {})
    
    # Extract the actual values from the parameter dictionaries
    def get_param_value(param_dict):
        if isinstance(param_dict, dict) and 'default' in param_dict:
            return param_dict['default']
        return param_dict

    # Extract only the parameters that AIRFlow accepts
    config = {
        'design': get_param_value(params.get('design', 'gcd')),
        'pdk': get_param_value(params.get('pdk', 'sky130')),
        'tools': get_param_value(params.get('tools', 'cm')),
        'env': get_param_value(params.get('env', 'bwrc')),
        'extra_args': get_param_value(params.get('extra_args', ''))
    }
    
    # If we have dag_run.conf, it overrides the params
    dag_run = context.get('dag_run')
    if dag_run and dag_run.conf:
        # Only update with accepted parameters
        for key in ['design', 'pdk', 'tools', 'env', 'extra_args']:
            if key in dag_run.conf:
                config[key] = get_param_value(dag_run.conf[key])
    
    return AIRFlow(**config)

def main():
    """Main entry point for hammer-vlsi command line tool."""
    CLIDriver().main()

def generic_task_callable(task_name, **context):
    # Create flow directly in the task
    flow = create_flow(**context)
    sys.argv = ['hammer-vlsi']

    if task_name == "build":
        sys.argv.extend(["build", "--obj_dir", flow.OBJ_DIR, "-e", flow.ENV_YML])
        for conf in flow.PROJ_YMLS:
            if conf:
                sys.argv.extend(["-p", conf])
    elif task_name == "clean":
        if os.path.exists(flow.OBJ_DIR):
            subprocess.run(f"rm -rf {flow.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)
            return "Clean completed"
    else:
        raise ValueError(f"Unknown task: {task_name}")

    print(f"Running task {task_name} with arguments: {sys.argv}")

    try:
        result = subprocess.run(sys.argv, check=True, capture_output=True, text=True)
        print(f"Task {task_name} completed successfully. Output:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running task {task_name}. Command: {e.cmd}")
        print(f"Exit code: {e.returncode}")
        print(f"Error output:\n{e.stderr}")
        raise

# Define tasks
with DAG(
    'hammer_vlsi',
    default_args={
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2024, 1, 1),
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
    schedule_interval=None,
    catchup=False,
    render_template_as_native_obj=True,
    params={
        'design': {
            'type': 'string',
            'default': 'gcd',
            'title': 'Design Name',
            'description': 'Name of the design to process'
        },
        'pdk': {
            'type': 'string',
            'default': 'sky130',
            'enum': ['sky130', 'asap7', 'nangate45'],
            'title': 'Process Design Kit',
            'description': 'PDK to use for the design'
        },
        'tools': {
            'type': 'string',
            'default': 'cm',
            'enum': ['cm', 'genus', 'innovus'],
            'title': 'Tool Flow',
            'description': 'EDA tools to use'
        },
        'target': {
            'type': 'string',
            'default': 'build',
            'enum': ['build', 'sim_rtl', 'syn', 'par', 'clean'],
            'title': 'Target',
            'description': 'Target action to perform'
        },
        'env': {
            'type': 'string',
            'default': 'bwrc',
            'title': 'Environment',
            'description': 'Environment configuration to use'
        },
        'extra_args': {
            'type': 'string',
            'default': '',
            'title': 'Extra Arguments',
            'description': 'Additional command line arguments'
        }
    }
) as dag:
    
    # Define tasks using updated generic_task_callable
    build_task = PythonOperator(
        task_id='build_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'build'},
        provide_context=True,
    )

    sim_rtl_task = PythonOperator(
        task_id='sim_rtl_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'sim_rtl'},
        provide_context=True,
    )

    syn_task = PythonOperator(
        task_id='syn_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'syn'},
        provide_context=True,
    )

    par_task = PythonOperator(
        task_id='par_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'par'},
        provide_context=True,
    )

    clean_task = PythonOperator(
        task_id='clean_task',
        python_callable=generic_task_callable,
        op_kwargs={'task_name': 'clean'},
        provide_context=True,
    )

    # Task dependencies
    [build_task, sim_rtl_task, syn_task, par_task, clean_task]

# Make DAG available to Airflow
globals()['hammer_vlsi'] = dag
