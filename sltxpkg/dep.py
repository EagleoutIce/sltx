import glob
import os
import re
import shutil
import sys
from concurrent import futures
from subprocess import PIPE, Popen  # execution
from pathlib import Path
from typing import List

import sltxpkg.globals as sg
from sltxpkg.config import load_dependencies_config, write_to_log
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_CREATE_DIRS,
                             C_DRIVER_LOG, C_DRIVER_PATTERNS, C_DRIVERS,
                             C_RECURSIVE, C_TEX_HOME, C_DOWNLOAD_DIR,
                             DEFAULT_CONFIG, print_idx)
import sltxpkg.util as su
from sltxpkg import dep

loaded = []


class Dependency:
    """
    A dependency based on flo's model that allows being passed to a driver.
    """
    download_dir: None

    def __init__(self, name: str = None, driver: str = None, url: str = None):
        self.name = name
        self.driver = driver
        self.url = url


class SltxDepConfig:
    target: str
    grab: dict
    dependencies: List[Dependency]

    def __init__(self):
        # TODO Check if this applies to python conventions.
        self.dependencies = []


def detect_driver(idx: str, url: str):
    print_idx(idx, " - Autodetecting driver...")
    for key, patterns in sg.configuration[C_DRIVER_PATTERNS].items():
        for pattern in patterns:
            if re.search(pattern, url):
                return key
    print_idx(idx, " ! No driver found...")
    sys.exit(1)


def split_grab_pattern(pattern: str, default_target: str) -> (str, str):
    parts = pattern.split('=>', 1)
    return (parts[0], default_target if len(parts) == 1 else parts[1])


def grab_from(idx: str, path: str, data: dict, target: str, key: str, grabber) -> bool:
    if key not in data:
        print_idx(idx, " ! Key '" + key + "' not found. Won't grab any...")
        return False

    grabs = []
    for grab_pattern in data[key]:
        pattern = split_grab_pattern(grab_pattern, target)
        # maybe forbid level up?
        grabs.extend(map(lambda x, pattern=pattern: (x, pattern[1]), glob.glob(os.path.join(
            path, pattern[0]), recursive=True)))

    # TODO: rel path for files?
    # extra so i can setup installer afterwards more easily
    print_idx(idx, " > Grabbing the follwing for installation:",
              [os.path.relpath(f[0], path) for f in grabs])
    for grab in grabs:
        grabber(grab, target, path)
    return True


def f_grab_files(data: (str, str), target: str, path: str):
    file_target = os.path.join(target, data[1]) if data[1] != target else os.path.join(
        data[1], os.path.relpath(data[0], path))
    Path(file_target).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(data[0], file_target)


def f_grab_dirs(data: (str, str), target: str, path: str):
    if sys.version_info < (3, 8, 0):
        print("Python version below 3.8, falling back with distutils!")
        import distutils.dir_util as du

    # only choose relative path
    dir_target = os.path.join(target, data[1]) if data[1] != target else os.path.join(
        data[1], os.path.relpath(data[0], path))
    Path(dir_target).parent.mkdir(parents=True, exist_ok=True)
    if sys.version_info >= (3, 8, 0):  # we have exist is ok
        shutil.copytree(data[0], dir_target, dirs_exist_ok=True)
    else:
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


def grab_stuff(idx: str, dep_name: str, target_dir: str, dep_dict: SltxDepConfig, target: str):
    # TODO CONTINUE HERE
    print_idx(idx, " > Grabbing dependencies for " + dep_name)
    print_idx(idx, "   - Grabby-Grab-Grab files from \"" + target_dir + "\"...")
    got_files = grab_from(idx, target_dir, dep_dict, target,
                          'files', f_grab_files)
    print_idx(idx, " - Grabby-Grab-Grab dirs from \"" + target_dir + "\"...")
    got_dirs = grab_from(idx, target_dir, dep_dict, target,
                         'dirs', f_grab_dirs)
    if not got_files and not got_dirs:
        print_idx(idx, " ! No grabs performed!")
        write_to_log("No grabs performed for: " + dep_name)


def get_target_dir(dep_config: Dependency, dep_name: str, driver: str):
    download_dir = dep_config.download_dir if dep_config.download_dir is not None else sg.configuration[C_DOWNLOAD_DIR]
    return sg.configuration[C_DRIVERS][driver]["target-dir"].format(download_dir=download_dir, dep_name=dep_name)


def recursive_dependencies(idx: str, driver_target_dir: str, data: dict, dep_name: str, target: str):
    # This is executed after the current dependency has been downloaded and before the files are being grabbed.
    # This allows loading the needed dependencies concurrently to grabbing the files. As we are currently not supporting
    # Multiple dependency files, we just don't use this function.
    # TODO Change this as this is currently not supported.
    if 'dep' not in data:
        print_idx(idx, "No 'dep' key found for dep: " + dep_name +
                  " using the default (" + sg.DEFAULT_DEPENDENCY + ")")
        data['dep'] = sg.DEFAULT_DEPENDENCY
    dep_files = glob.glob(os.path.join(
        driver_target_dir, data['dep']), recursive=True)
    print_idx(idx, " - Found dep-config:", dep_files)

    if len(dep_files) <= 0:
        return

    new_dependencies = {}
    for dep_file in dep_files:
        new_dependencies = load_dependencies_config(dep_file, new_dependencies)

    _install_dependencies(idx, new_dependencies, target)


def use_driver(idx: str, dep_config: SltxDepConfig, dep_name: str, driver: str, url: str, target: str,
               args: str = None):
    # default no arguments
    # Add args for driver.
    # TODO Args are currently not supported.
    data = dict()
    data["args"] = "" if "args" not in data else args
    driver_data = sg.configuration[C_DRIVERS][driver]
    # Prepare the driver command.
    command = driver_data["command"].format(
        **data, **sg.configuration, dep_name=dep_name)
    # TODO Dis data stuff not right. CONTINUE HERE
    driver_target_dir = get_target_dir(data, dep_name, driver)
    if os.path.isdir(driver_target_dir) and driver_data["needs-delete"]:
        print_idx(idx, " - Target folder", driver_target_dir,
                  "exists. Will be deleted as the driver needs this")
        shutil.rmtree(driver_target_dir)
    # Execute the driver command.
    print_idx(idx, " > Executing:", command)
    feedback = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    return_code = feedback.wait()
    write_proc_to_log(idx, feedback.stdout, False)
    if return_code != 0:
        print_idx(idx, " - Error-Log of Driver:")
    write_proc_to_log(idx, feedback.stderr, return_code != 0)
    # Parse the sltx config.
    dep_config = parse_sltx_dep_config_from_target_dir(idx, driver_target_dir)

    # Proceed with the downloaded files.
    if sg.configuration[C_RECURSIVE]:
        # Recursively fetch the new dependencies
        _install_dependencies(idx, dep_config.dependencies, target, first=False)

    if return_code != 0:
        print_idx(idx, " ! Driver failed with code", feedback, "exiting.")
        sys.exit(return_code)

    # TODO Now the recursive stuff works and we just have to grab our files :) CONTINUE HERE 2
    grab_stuff(idx, dep_name, driver_target_dir, data, target)


def parse_unknown_driver(idx: str, driver: str, data: dict) -> str:
    """
    Parses an unknown driver by checking whether auto detection is enabled and if so uses the first level of data to
    auto detect the driver. If no one is found an InvalidSltxConfigException will be raised.

    :param idx: The id of the current level
    :param driver: The unknown driver
    :param data: The attached data
    :return: The detected driver
    """
    if not sg.configuration[C_AUTODETECT_DRIVERS]:
        # Auto detecting not enabled.
        print_idx(idx, " ! Unknown driver and auto detection disabled!")
        raise InvalidSltxConfigException("unknown driver: %s" % driver)
    else:
        # Auto detect driver from level 1.
        # TODO Adjust driver detection so that it uses multiple inputs and compares the detection results.
        detected_driver = None
        for data in data[driver]:
            detected_driver = detect_driver(idx, data)
            if detected_driver is not None:
                break
        if detected_driver is None:
            # No driver could be auto detected.
            print_idx(idx, " ! Could not detect driver:", driver)
            raise InvalidSltxConfigException("unknown driver: %s" % driver)
        return detected_driver


def parse_dependencies_using_git(idx: str, data: dict) -> List[Dependency]:
    """
    Parses the dependencies using git driver. The first level of data is the host, the second one the user and the third
    one the repository.

    :param idx: The idx
    :param data: The data attached to the git driver
    :return: The parsed dependencies
    """
    deps = []
    for host in data:
        users = data[host]
        # Check for github and gitlab as they are common and very special ones <3.
        if host == "github":
            host = "https://github.com"
        elif host == "gitlab":
            host = "https://gitlab.com"
        # Proceed with the users.
        for user in users:
            repos = users[user]
            # And finally check the particular repos.
            for repo in repos:
                props = repos[repo]
                # Build the dependency.
                url = "%s/%s/%s" % (host, user, repo)
                dependency = Dependency(name=repo, driver="git", url=url)
                if "download-dir" in props:
                    dependency.download_dir = props["download-dir"]
                deps.append(dependency)
    return deps


def parse_dependencies(idx: str, driver: str, data: dict) -> List[Dependency]:
    """
    Parses dependencies attached to a driver. The method highly depends on the driver: For git the url is built from
    the following three levels. For other drivers currently urls are expected on the first level.

    :param idx: The id of the current dependency level
    :param driver: The driver name
    :param data: The data attached to the driver
    :return: The parsed dependencies
    """
    deps = []
    if driver == "git":
        # Build from first two levels
        deps.extend(parse_dependencies_using_git(idx, data))
    else:
        # Parse the dependencies without using driver specific action.
        for data_content in data:
            props = data[data_content]
            dependency = Dependency(name=data_content, driver=driver, url=data_content)
            if "download-dir" in props:
                dependency.download_dir = props["download-dir"]
            # Just parse the data content as an url
            # TODO Check if the passed url is in url format.
            # TODO Decide how we want to name the dependency if we only get an url.
            deps.append(dependency)
    return deps


def parse_sltx_dep_config(idx: str, config: dict) -> SltxDepConfig:
    """
    Parses the dependencies. It has a hierarchical structure with the following layers:
    Drivers -> Dependencies
    The structure of the dependencies depend on the platform. For the git driver it looks like the following:
    Platform (github, gitlab) -> User (EagleOutIce) -> Repository (color-palettes)

    :param idx: The id of the current dependency level
    :param config: The config loaded as yaml
    :return: The parsed sltx config
    """
    print_idx(idx, "Parsing sltx config...")
    res = SltxDepConfig()
    # Read the target field.
    if "target" not in config:
        print_idx(idx, "Missing required target field in dep config.")
        raise InvalidSltxConfigException("missing required target field")
    res.target = config["target"]
    # Read the grab field.
    if "grab" not in config:
        print_idx(idx, "Missing required grab field in dep config.")
        raise InvalidSltxConfigException("missing required grab field")
    res.grab = config["grab"]
    # Parse the dependencies.
    if "dependencies" not in config:
        print_idx(idx, "No dependencies supplied.")
    else:
        drivers = config["dependencies"]
        for driver in drivers:
            # Proceed with each driver.
            if driver not in sg.configuration[C_DRIVERS]:
                driver = parse_unknown_driver(idx, driver, drivers[driver])
            print_idx(idx, "Using driver:", driver)
            parsed_deps = parse_dependencies(idx, driver, drivers[driver])
            print_idx(idx, "Parsed %d dependencies." % len(parsed_deps))
            res.dependencies.extend(parsed_deps)
    # Check for optional download dir overwrite
    if "download-dir" in config:
        res.download_dir = config["download-dir"]

    print_idx(idx, "Finished parsing sltx dep config.")
    return res


def parse_sltx_dep_config_from_target_dir(idx: str, target_dir: str) -> SltxDepConfig:
    """
    Parses the sltx config that lies in the target directory.

    :param idx: The id of the current dependency level
    :param target_dir: The target directory
    :return: The parsed sltx config
    """
    dep_path = os.path.join(target_dir, sg.DEFAULT_DEPENDENCY)
    # I really don't get the load dep config stuff.
    dep_config_dict = su.load_yaml(dep_path)
    return parse_sltx_dep_config(idx, dep_config_dict)


def install_dependency(name: str, idx: str, dep_to_install: Dependency, target: str):
    print_idx(idx, "Loading \"" + name + "\"")
    print_idx(idx, " - Loading from: \"" + dep_to_install.url + "\"")
    print_idx(idx, " - Using driver: \"" + dep_to_install.driver + "\"")

    if name in loaded:
        print_idx(idx, " > Skipping retrieval", name, " as it was already loaded by another dependency.")
        target_dir = get_target_dir(dep_to_install, name, dep_to_install.driver)
        # TODO Parse the sltx dep config
        grab_stuff(idx, name, target_dir, dep_dict, target)
        return
    loaded.append(name)

    if driver not in sg.configuration[C_DRIVERS]:
        print_idx(idx, " ! The selected driver is unknown. Loaded:",
                  sg.configuration[C_DRIVERS])
        sys.exit(2)

    use_driver(idx, dep_dict, name, driver, url, target)


def _install_dependencies(idx: str, deps: List[Dependency], target: str, first: bool = False):
    with futures.ThreadPoolExecutor(max_workers=sg.args.threads) as pool:
        runners = []
        for i, dep_to_install in enumerate(deps):
            new_idx = str(i) if first else idx + "." + str(i)
            runners.append(pool.submit(install_dependency, dep_to_install.name, new_idx, dep_to_install, target))
        futures.wait(runners)
        for runner in runners:
            if runner.result() is not None:
                print(runner.result())


def install_dependencies(install_target: str = su.get_sltx_tex_home()):
    dep_config = parse_sltx_dep_config("INIT", sg.dependencies)

    write_to_log("====Dependencies for:" + dep_config.target + "\n")
    print()
    print("Dependencies for:", dep_config.target)
    print("Installing to:", install_target)
    print()

    _install_dependencies(0, sg.dependencies, install_target, first=True)

    # all installed
    if sg.configuration[C_CLEANUP]:
        print("> Cleaning up the download directory, as set.")
        shutil.rmtree(sg.configuration[C_DOWNLOAD_DIR])
    print("Loaded:", dep.loaded)
    if not sg.configuration[C_RECURSIVE]:
        print("Recursion was disabled.")
    print("Dependency installation for",
          dep_config.target, "completed.")


class InvalidSltxConfigException(Exception):
    """
    Exception that is being raised when the sltx config contains invalid or missing fields.
    """

    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return "Invalid sltx config: %s" % self.reason
