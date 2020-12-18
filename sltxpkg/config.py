import os
import sys

import yaml

from sltxpkg import globals as sg
from sltxpkg import util as su
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_CREATE_DIRS,
							 C_DOWNLOAD_DIR, C_DRIVER_LOG, C_DRIVER_PATTERNS,
							 C_DRIVERS, C_TEX_HOME, C_WORKING_DIR, C_CACHE_DIR,
							 DEFAULT_CONFIG)


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


def _assure_dir(name: str, target_path: str, create: bool):
	if not os.path.isdir(target_path):
		if create:
			print(">", name, ":", target_path, "not found. Creating...")
			os.makedirs(target_path)
		else:
			print("! Not allowed to create" + name + ". Exit")
			sys.exit(1)


def assure_dirs():
	sg.configuration[C_TEX_HOME] = su.get_sltx_tex_home()  # expansion
	create = sg.configuration[C_CREATE_DIRS]
	_assure_dir('Tex-Home', sg.configuration[C_TEX_HOME], create)

	for config, name in [(C_WORKING_DIR, 'Working-Dir'), (C_DOWNLOAD_DIR, 'Download-Dir'),
			(C_CACHE_DIR, 'Cache-Dir')]:
		sg.configuration[config] = os.path.expanduser(sg.configuration[config])  # expansion
		_assure_dir(name, sg.configuration[config], create)

