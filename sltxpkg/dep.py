import glob
import os
import re
import shutil
import sys
from concurrent import futures
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Tuple  # execution

import sltxpkg.globals as sg
import sltxpkg.util as su
from sltxpkg.config import load_dependencies_config, write_to_log
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_DOWNLOAD_DIR, C_DRIVER_PATTERNS,
                             C_DRIVERS, C_RECURSIVE, print_idx)
from sltxpkg.log_control import LOGGER

loaded = []


def detect_driver(idx: str, url: str) -> str:
    """Tries to match the given patterns to [description]
    This could be optimized by pre-compile the given patterns.

    Args:
        idx (str): the current index number for logging
        url (str): the url to adapt the driver from

    Returns:
        (str): The driver key to use
    """
    print_idx(idx, " - Auto-detecting driver...")
    for key, patterns in sg.configuration[C_DRIVER_PATTERNS].items():
        for pattern in patterns:
            if re.search(pattern, url):
                return key
    print_idx(idx, " ! No driver found...")
    sys.exit(1)


def split_grab_pattern(pattern: str, default_target: str) -> Tuple[str, str]:
    """Performes splits on grab patterns ("source=>target")
       will fill in the given default target, if split does not present one

    Args:
        pattern (str): The pattern to split
        default_target (str): The target to be auto-filled if none given

    Returns:
        (str,str): pattern and pair
    """
    parts = pattern.split('=>', 1)
    target = default_target if len(parts) == 1 else parts[1]
    return parts[0], target


class DependencyProfileException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def extend_grab_from_local(idx: str, driver_target_dir: str, data: dict) -> Tuple[list, list]:
    """May install extra profiles

       This method will check for a local dep file, and if present
       check for a profiles key. if present it will check for a selected profile in the data dict.
       If so, select it, if none, set the default
    Args:
        idx (str): index to use in multithreading
        driver_target_dir (str): target dir of the current driver
        data (str): data dict for local configuration
    Returns:
        (list,list) - a list of additional dependencies in the format 'files, folder'
    """
    if 'dep' not in data:
        dep = sg.DEFAULT_DEPENDENCY
    else:
        dep = data['dep']
    dep_files = glob.glob(os.path.join(driver_target_dir, dep), recursive=True)
    if len(dep_files) <= 0:
        return [], []

    # load file and check for default
    # TODO: avoid reloading if recursive?
    file_profiles = {}
    for dep_file in dep_files:
        file_profiles = load_dependencies_config(dep_file, file_profiles)

    if 'profiles' not in file_profiles:
        return [], []

    file_profiles = file_profiles['profiles']
    # Note: I do want always a default profile so it makes live easier for me
    if 'default' not in file_profiles:
        raise DependencyProfileException(
            'No default profile for enlisted profiles. Found: ' + str(file_profiles))
    if 'profile' in data:
        requested_profile = data['profile']
        if requested_profile not in file_profiles:
            raise DependencyProfileException('Requested profile (' + requested_profile + ') not found. Found: ' +
                                             str(file_profiles))
    else:
        requested_profile = 'default'
    added_profiles: dict = file_profiles[requested_profile]
    print_idx(idx, ' > Loaded profile (' +
              requested_profile + '): ' + str(added_profiles))
    # TODO: this may be beautified
    grab_files = added_profiles['grab-files'] if 'grab-files' in added_profiles else ""
    grab_dirs = added_profiles['grab_dirs'] if 'grab_dirs' in added_profiles else ""
    return grab_files, grab_dirs


def grab_from(idx: str, path: str, data: dict, target: str, key: str, grabber, extras: list) -> bool:

    if key not in data:
        if len(extras) == 0:
            print_idx(idx, " ! Key '" + key + "' not found. Won't grab any...")
            return False
        else:
            data[key] = extras
    else:
        data[key].extend(extras)

    grabs = []
    for grab_pattern in set(data[key]):
        cur_grab_pattern = split_grab_pattern(grab_pattern, target)
        # maybe forbid level up?
        grabs.extend(map(lambda x, pattern=cur_grab_pattern: (x, pattern[1]),
                         glob.glob(os.path.join(path, cur_grab_pattern[0]), recursive=True)))

    # extra so i can setup installer afterwards more easily
    print_idx(idx, " > Grabbing the following for installation: "
              + str([os.path.relpath(f[0], path) for f in grabs]))
    for grab in grabs:
        grabber(grab, target, path)
    return True


def f_grab_files(data: Tuple[str, str], target: str, path: str):
    file_target = os.path.join(target, data[1]) if data[1] != target else os.path.join(
        data[1], os.path.relpath(data[0], path))
    Path(file_target).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(data[0], file_target)


def f_grab_dirs(data: Tuple[str, str], target: str, path: str):
    # only choose relative path
    dir_target = os.path.join(target, data[1]) if data[1] != target else os.path.join(
        data[1], os.path.relpath(data[0], path))
    Path(dir_target).parent.mkdir(parents=True, exist_ok=True)
    if sys.version_info >= (3, 8, 0):  # we have exist is ok
        shutil.copytree(data[0], dir_target, dirs_exist_ok=True)
    else:
        LOGGER.info("Python version below 3.8, falling back with distutils!")
        import distutils.dir_util as du
        du.copy_tree(data[0], dir_target)


def write_proc_to_log(idx: str, stream, mirror: bool):
    while True:
        line = stream.readline()
        if not line:
            break
        line_utf8 = line.decode('utf-8')
        write_to_log(line_utf8)
        if mirror:
            print_idx(idx, line_utf8)


def grab_stuff(idx: str, dep_name: str, target_dir: str, data: dict, target: str):

    extra_files, extra_dirs = extend_grab_from_local(idx, target_dir, data)

    print_idx(idx, " > Grabbing dependencies for " + dep_name)
    print_idx(idx, "   - Grabby-Grab-Grab files from \"" + target_dir + "\"...")
    got_files = grab_from(idx, target_dir, data, target,
                          'grab-files', f_grab_files, extra_files)
    print_idx(idx, " - Grabby-Grab-Grab dirs from \"" + target_dir + "\"...")
    got_dirs = grab_from(idx, target_dir, data, target,
                         'grab-dirs', f_grab_dirs, extra_dirs)
    if not got_files and not got_dirs:
        print_idx(idx, " ! No grabs performed!")
        write_to_log("No grabs performed for: " + dep_name)


def get_target_dir(data: dict, dep_name: str, driver: str):
    return sg.configuration[C_DRIVERS][driver]["target-dir"].format(
        **data, **sg.configuration, dep_name=dep_name)


def recursive_dependencies(idx: str, driver_target_dir: str, data: dict, dep_name: str, target: str):
    if 'dep' not in data:
        print_idx(idx, "No 'dep' key found for dep: " + dep_name +
                  " using the default (" + sg.DEFAULT_DEPENDENCY + ")")
        data['dep'] = sg.DEFAULT_DEPENDENCY
    dep_files = glob.glob(os.path.join(
        driver_target_dir, data['dep']), recursive=True)
    print_idx(idx, " - Found dep-config: " + str(dep_files))

    if len(dep_files) <= 0:
        return

    new_dependencies = {}
    for dep_file in dep_files:
        new_dependencies = load_dependencies_config(dep_file, new_dependencies)

    _install_dependencies(idx, new_dependencies, target)


def use_driver(idx: str, data: dict, dep_name: str, driver: str, target: str):
    # default no arguments
    if "args" not in data:
        data["args"] = ""
    driver_data = sg.configuration[C_DRIVERS][driver]
    command = driver_data["command"].format(
        **data, **sg.configuration, dep_name=dep_name)
    driver_target_dir = get_target_dir(data, dep_name, driver)
    if driver_data["needs-delete"] and os.path.isdir(driver_target_dir):
        print_idx(idx, " - Target folder " + driver_target_dir +
                  "exists. Will be deleted as the driver needs this")
        shutil.rmtree(driver_target_dir)

    if driver_data["needs-create"] and not os.path.isdir(driver_target_dir):
        print_idx(idx, " - Target folder " +
                  driver_target_dir + " needs creation")
        os.makedirs(driver_target_dir)

    print_idx(idx, " > Executing: " + command)
    with Popen(command, stdout=PIPE, stderr=PIPE, shell=True) as feedback:
        return_code = feedback.wait()
        write_proc_to_log(idx, feedback.stdout, False)
        if return_code != 0:
            print_idx(idx, " - Error-Log of Driver:")
        write_proc_to_log(idx, feedback.stderr, return_code != 0)

    if sg.configuration[C_RECURSIVE]:
        recursive_dependencies(idx, driver_target_dir, data, dep_name, target)

    if return_code != 0:
        print_idx(idx, " ! Driver failed with code" +
                  str(feedback) + "exiting.")
        sys.exit(return_code)

    grab_stuff(idx, dep_name, driver_target_dir, data, target)


def install_dependency(name: str, idx: str, data: dict, target: str):
    print_idx(idx, 'Loading "' + name + '"')

    if "url" not in data:
        print_idx(idx, " ! The dependency did not have an url-tag attached")
        exit(1)

    url = data["url"]
    print_idx(idx, ' - Loading from: "' + url + '"')
    if "driver" not in data:
        if not sg.configuration[C_AUTODETECT_DRIVERS]:
            print_idx(idx, " ! No driver given and auto-detection disabled!")
        else:
            data["driver"] = detect_driver(idx, url)

    driver = data["driver"]
    print_idx(idx, " - Using driver: \"" + driver + "\"")

    if name in loaded:
        print_idx(idx, " > Skipping retrieval " + name +
                  " as it was already loaded by another dep.")
        grab_stuff(idx, name, get_target_dir(data, name, driver), data, target)
        return

    loaded.append(name)

    if driver not in sg.configuration[C_DRIVERS]:
        print_idx(idx, ' ! The selected driver is unknown. Loaded:' +
                  sg.configuration[C_DRIVERS])
        sys.exit(2)
    use_driver(idx, data, name, driver, target)


def _finish_runners(runners: list):
    futures.wait(runners)
    for runner in runners:
        if runner.result() is not None:
            LOGGER.info(runner.result())


def _install_dependencies(idx: str, dep_dict: dict, target: str, first: bool = False):
    """Will install dependencies in an multi-threaded environment and may be called recursively

    Args:
        idx (str): The index to be run in (will start with 0)
        dep_dict (dict): Dependencies to fetch with this run
        target (str): The target directory for the fetch
        first (bool, optional): Flag for the initial run. Defaults to False.
    """
    if 'dependencies' not in dep_dict:
        return

    with futures.ThreadPoolExecutor(max_workers=sg.args.threads) as pool:
        runners = []
        for i, dep in enumerate(dep_dict['dependencies']):
            runners.append(pool.submit(install_dependency, dep, str(i) if first else idx + "." + str(i),
                                       dep_dict['dependencies'][dep], target))
        _finish_runners(runners)


def _install_dependencies_guard():
    """Cheap command line guard which will check for valid keys
    """
    if "target" not in sg.dependencies or "dependencies" not in sg.dependencies:
        LOGGER.error(
            "The dependency-file must supply a 'target' and an 'dependencies' key!")
        sys.exit(1)


def _install_dependencies_cleanup():
    """This will be run after the requested dependencies have been installed.
    """
    if sg.configuration[C_CLEANUP]:
        LOGGER.info("> Cleaning up the download directory, as set.")
        shutil.rmtree(sg.configuration[C_DOWNLOAD_DIR])

    LOGGER.info("Loaded: " + str(loaded))
    if not sg.configuration[C_RECURSIVE]:
        LOGGER.info("Recursion was disabled.")

    LOGGER.info("Dependency installation for %s completed.",
                sg.dependencies["target"])


def install_dependencies(target: str = su.get_sltx_tex_home()) -> None:
    """Download and unpack given dependencies to the given target directory

    Args:
        target (str, optional): The target folder. Defaults to su.get_sltx_tex_home().
    """
    _install_dependencies_guard()

    write_to_log("====Dependencies for:" + sg.dependencies["target"] + "\n")
    LOGGER.info("\nDependencies for: " + sg.dependencies["target"])
    LOGGER.info("Installing to: %s\n", target)

    _install_dependencies('0', sg.dependencies, target, first=True)
    _install_dependencies_cleanup()
