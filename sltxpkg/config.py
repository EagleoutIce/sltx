import yaml
import os
import sys
from sltxpkg import globals as sg, util as su
from sltxpkg.globals import DEFAULT_CONFIG, C_AUTODETECT_DRIVERS, C_TEX_HOME, C_WORKING_DIR, C_CREATE_DIRS, C_CLEANUP, C_DRIVER_LOG, C_DRIVERS, C_DRIVER_PATTERNS

def write_to_log(data: str):
    if sg.configuration[C_DRIVER_LOG].strip():
        with open(sg.configuration[C_DRIVER_LOG], 'a') as f:
            f.write(data)
            if not data.endswith('\n'):
                f.write("\n")


def load_configuration(file: str):
    y_conf = su.load_yaml(file)
    sg.configuration = {**sg.configuration, **y_conf}


def load_dependencies_config(file: str, target: dict):
    y_dep = su.load_yaml(file)
    return {**target, **y_dep}


def assure_dirs():
    target_path = su.get_tex_home()
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
