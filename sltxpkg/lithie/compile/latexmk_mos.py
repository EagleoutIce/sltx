import os
from sys import platform

from importlib_resources import files

import sltxpkg.data.latexmk.configs
import sltxpkg.util as su
from sltxpkg import globals as sg
from sltxpkg.globals import LOGGER

# We have to configure latexmk configuration-files os-dependent
# NOTE: no cygwin support


class UnknownPlatformException(Exception):
    pass


def get_root() -> str:
    """Return the root folder of the current platform

    Returns:
        str: root folder of the current platform
    """
    if platform == "linux":
        return os.path.expandvars("$HOME/.latexmkrc")
    elif platform == "darwin":
        return os.path.expandvars("$HOME/.latexmkrc")
    elif platform == "win32":
        return "C:\\latexmk\\LatexMk"
    else:
        raise UnknownPlatformException("Unknown platform")


def get_config(name: str) -> str:
    """Get local mkrc configuration

    Args:
        name (str): The required configuration file name.

    Returns:
        str: The content of the requested file.
    """
    return files(sltxpkg.data.latexmk.configs).joinpath(name + '.mkrc').read_text()


def append_local2global_config(name: str) -> None:
    """Appends an included configuration to the system configuration

    Args:
        name (str): The requirested configuration
    """
    __append_to_global_config(get_config(name), name)


def __append_to_global_config(text: str, guard: str) -> None:
    file = get_root()
    start_guard = "# sltx START " + guard
    mode = 'a'

    if os.path.isfile(file) and su.file_contains(file, start_guard):
        if sg.args.verbose:
            LOGGER.info(
                "Global latexmk config already contains config for %s. Skipping.", guard)
        return

    with open(file, mode) as f:
        f.write("\n" + start_guard + "\n")
        f.writelines(text)
        f.write("# sltx END " + guard + "\n")
