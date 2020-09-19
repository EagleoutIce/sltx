import yaml
import os
import sys
from sltx_globals import DEFAULT_CONFIG, C_DRIVER_LOG, C_TEX_HOME, C_WORKING_DIR, C_CREATE_DIRS, C_CLEANUP, C_AUTODETECT_DRIVERS, C_DRIVERS, C_DRIVER_PATTERNS
import sltx_globals as sg

def write_to_log(data: str):
    if sg.configuration[C_DRIVER_LOG].strip():
        with open(sg.configuration[C_DRIVER_LOG], 'a') as f:
            f.write(data)


def load_configuration(file: str):
    with open(file, 'r') as yaml_file:
        # FullLoader only available for 5.1 and above:
        if float(yaml.__version__[:yaml.__version__.rfind(".")]) >= 5.1:
            y_conf = yaml.load(yaml_file, Loader=yaml.FullLoader)
        else:
            y_conf = yaml.load(yaml_file)
        sg.configuration = {**sg.configuration, **y_conf}


def load_dependencies_config(file: str):
    with open(file, 'r') as yaml_file:
        # FullLoader only available for 5.1 and above:
        if float(yaml.__version__[:yaml.__version__.rfind(".")]) >= 5.1:
            y_dep = yaml.load(yaml_file, Loader=yaml.FullLoader)
        else:
            y_dep = yaml.load(yaml_file)
        sg.dependencies = {**sg.dependencies, **y_dep}
    print("Loaded dependencies:", sg.dependencies)


def assure_dirs():
    target_path = os.path.expanduser(sg.configuration[C_TEX_HOME])
    create = sg.configuration[C_CREATE_DIRS]
    if not os.path.isdir(target_path):
        if create:
            print("> Tex-Home-Dir", target_path, "not found. Creating...")
            os.makedirs(target_path)
        else:
            print("! Not allowed to create texhome. Exit")
            sys.exit(1)
    sg.configuration[C_TEX_HOME] = target_path  # expansion
    target_path = os.path.expanduser(sg.configuration[C_WORKING_DIR])
    if not os.path.isdir(target_path):
        if create:
            print("> Working-Dir", target_path, "not found. Creating...")
            os.makedirs(target_path)
        else:
            print("! Not allowed to create working-dir. Exit")
            sys.exit(1)
    sg.configuration[C_WORKING_DIR] = target_path  # expansion
