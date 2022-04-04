import mmap
import os
import re
from sys import platform
from time import localtime, strftime

import yaml
from importlib_resources import files

import sltxpkg.data
import sltxpkg.globals as sg


def default_texmf() -> str:
    """Default texmf-paths

    Returns:
        str: The default texmf-path for the given platform
    """
    if platform == "linux" or platform == "linux2":
        return "~/texmf"
    elif platform == "darwin":
        return "~/Library/texmf"
    elif platform == "win32":
        return "~/texmf"
    else:
        return "~/texmf"


def get_version() -> str:
    """Returns the version number from the included package files

    Returns:
        str: The version number in string format.
    """
    return files(sltxpkg.data).joinpath('version.info').read_text()


def load_yaml(file_path: str):
    with open(file_path, 'r') as yaml_file:
        # FullLoader only available for 5.1 and above:
        if float(yaml.__version__[:yaml.__version__.rfind('.')]) >= 5.1:
            return yaml.load(yaml_file, Loader=yaml.FullLoader)
        else:
            return yaml.load(yaml_file)  # type: ignore


def file_contains(path: str, txt: str):
    with open(path, 'rb', 0) as file, \
            mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
        return s.find(txt.encode('utf-8')) != -1


def get_now() -> str:
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


SANITIZE_PATTERN = re.compile('[^a-zA-Z0-9-]')


def sanitize_filename(text: str) -> str:
    return SANITIZE_PATTERN.sub('_', text)


def create_multiple_replacer(replacements: dict):
    replacements = dict((re.escape(k), v)
                        for k, v in replacements.items())
    rep_pattern = re.compile('|'.join(replacements.keys()))
    return lambda msg: rep_pattern.sub(lambda x: replacements[re.escape(x.group(0))], msg)
