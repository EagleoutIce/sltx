from sys import platform
from importlib_resources import files, as_file
import sltxpkg.data
import yaml

def default_texmf():
    if platform == "linux" or platform == "linux2":
        return "~/texmf"
    elif platform == "darwin":
        return "~/Library/texmf"
    elif platform == "win32":
        return "~/texmf"


def get_version():
    return files(sltxpkg.data).joinpath('version.info').read_text()

def load_yaml(file_path : str):
    with open(file_path, 'r') as yaml_file:
            # FullLoader only available for 5.1 and above:
        if float(yaml.__version__[:yaml.__version__.rfind(".")]) >= 5.1:
            return yaml.load(yaml_file, Loader=yaml.FullLoader)
        else:
            return yaml.load(yaml_file)