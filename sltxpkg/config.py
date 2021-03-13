import os
import sys

import yaml

from sltxpkg import globals as sg
from sltxpkg import util as su
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CACHE_DIR, C_CLEANUP,
                             C_CREATE_DIRS, C_DOWNLOAD_DIR, C_DRIVER_LOG,
                             C_DRIVER_PATTERNS, C_DRIVERS, C_TEX_HOME,
                             C_WORKING_DIR, DEFAULT_CONFIG)
from sltxpkg.log_control import LOGGER


def write_to_log(data: str):
    if sg.configuration[C_DRIVER_LOG].strip():
        with open(sg.configuration[C_DRIVER_LOG], 'a') as f:
            f.write(data)
            if not data.endswith('\n'):
                f.write("\n")


def load_configuration(file: str):
    """Apply given configuration file to the sltx config

    Args:
        file (str): The configuration file to load
    """
    y_conf = su.load_yaml(file)
    sg.configuration = {**sg.configuration, **y_conf}


def load_dependencies_config(file: str, target: dict) -> dict:
    """Apply given dependency file to the sltx dep list

    Args:
        file (str): The file to load
        target (dict): The target dependency-collection to append it to (won't be modified)

    Returns:
        dict: The target dict with the added dependencies
    """
    y_dep = su.load_yaml(file)
    return {**target, **y_dep}


def assure_dir(name: str, target_path: str, create: bool):
    if not os.path.isdir(target_path):
        if create:
            LOGGER.info("> %s: %s not found. Creating...", name, target_path)
            os.makedirs(target_path)
        else:
            LOGGER.error("! Not allowed to create " + name + ". Exit")
            sys.exit(1)


def assure_dirs():
    sg.configuration[C_TEX_HOME] = su.get_sltx_tex_home()  # expansion
    create = sg.configuration[C_CREATE_DIRS]
    assure_dir('Tex-Home', sg.configuration[C_TEX_HOME], create)

    for config, name in [(C_WORKING_DIR, 'Working-Dir'), (C_DOWNLOAD_DIR, 'Download-Dir'),
                         (C_CACHE_DIR, 'Cache-Dir')]:
        sg.configuration[config] = os.path.expanduser(
            sg.configuration[config])  # expansion
        assure_dir(name, sg.configuration[config], create)
