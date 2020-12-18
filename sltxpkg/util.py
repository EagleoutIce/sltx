import mmap
import os
from sys import platform
from time import localtime, strftime
import re

import yaml
from importlib_resources import as_file, files

import sltxpkg.data
import sltxpkg.globals as sg


def default_texmf():
	if platform == "linux" or platform == "linux2":
		return "~/texmf"
	elif platform == "darwin":
		return "~/Library/texmf"
	elif platform == "win32":
		return "~/texmf"


def get_version():
	return files(sltxpkg.data).joinpath('version.info').read_text()


def load_yaml(file_path: str):
	with open(file_path, 'r') as yaml_file:
		# FullLoader only available for 5.1 and above:
		if float(yaml.__version__[:yaml.__version__.rfind(".")]) >= 5.1:
			return yaml.load(yaml_file, Loader=yaml.FullLoader)
		else:
			return yaml.load(yaml_file)


def file_contains(path: str, txt: str):
	with open(path, 'rb', 0) as file, \
			mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
		return s.find(txt.encode('utf-8')) != -1


def get_now():
	return strftime("%Y-%m-%d__%H-%M-%S", localtime())


def get_default_conf() -> str:
	return os.path.expanduser(sg.DEFAULT_CONFIG)


def get_local_conf() -> str:
	return os.path.expanduser(sg.LOCAL_CONFIG)


def get_tex_home() -> str:
	return os.path.expanduser(default_texmf())


def get_sltx_tex_home() -> str:
	return os.path.expanduser(sg.configuration[sg.C_TEX_HOME].format(
		**sg.configuration, os_default_texmf=default_texmf()))

# For compile


def sanitize_filename(text: str):
	return re.sub('[^a-zA-Z0-9\-_]', '_', text)
