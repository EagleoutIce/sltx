import glob
import os
import re
import shutil
import sys
from concurrent import futures
from subprocess import PIPE, Popen  # execution

import sltxpkg.globals as sg
from sltxpkg.config import load_dependencies_config, write_to_log
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_CREATE_DIRS,
                             C_DRIVER_LOG, C_DRIVER_PATTERNS, C_DRIVERS,
                             C_RECURSIVE, C_TEX_HOME, C_WORKING_DIR,
                             DEFAULT_CONFIG, print_idx)

if sys.version_info < (3, 8, 0):
    print("Python version below 3.8, falling back with distutils!")
    import distutils.dir_util as du


loaded = []


def detect_driver(idx: str, url: str):
    print_idx(idx, " - Autodetecting driver...")
    for key, patterns in sg.configuration[C_DRIVER_PATTERNS].items():
        for pattern in patterns:
            if re.search(pattern, url):
                return key
    print_idx(idx, " ! No driver found...")
    sys.exit(1)


def grab_files_from(idx: str, path: str, data: dict):
    print_idx(idx, " - Grabby-Grab-Grab files from \"" + path + "\"...")
    if "grab-files" not in data:
        print_idx(idx, " ! Key 'grab-files' not found. Won't grab any files")
        return False

    files = []
    for grab_pattern in data["grab-files"]:
        # maybe forbid level up?
        files.extend(glob.glob(os.path.join(
            path, grab_pattern), recursive=True))
    # extra so i can setup installer afterwards more easily
    print_idx(idx, " > Grabbing the follwing files for installation:",
              [os.path.relpath(f, path) for f in files])
    for file in files:
        shutil.copy2(file, sg.configuration[C_TEX_HOME])
    return True


def grab_dirs_from(idx: str, path: str, data: dict):
    print_idx(idx, " - Grabby-Grab-Grab dirs from \"" + path + "\"...")
    if "grab-dirs" not in data:
        print_idx(idx, " ! Key 'grab-dirs' not found. Won't grab any directories")
        return False

    dirs = []
    for grab_pattern in data["grab-dirs"]:
        # maybe forbid level up?
        dirs.extend(glob.glob(os.path.join(
            path, grab_pattern), recursive=True))

    # extra so i can setup installer afterwards more easily
    print_idx(idx, " > Grabbing the follwing dirs for installation:", dirs)
    for dir in dirs:
        # if fails rethrow :D
        dir_target = os.path.join(
            sg.configuration[C_TEX_HOME], os.path.relpath(dir, path))
        if sys.version_info >= (3, 8, 0):
            # we have exist is ok
            shutil.copytree(dir, dir_target, dirs_exist_ok=True)
        else:
            # we use distutils
            du.copy_tree(dir, dir_target)
    return True


def write_proc_to_log(idx: int, stream, mirror: bool):
    while True:
        line = stream.readline()
        if not line:
            break
        line_utf8 = line.decode('utf-8')
        write_to_log(line_utf8)
        if mirror:
            print_idx(idx, line_utf8)


def grab_stuff(idx: str, dep_name: str, target_dir: str, data: dict):
    print_idx(idx, " > Grabbing dependencies for " + dep_name)
    got_files = grab_files_from(idx, target_dir, data)
    got_dirs = grab_dirs_from(idx, target_dir, data)
    if not got_files and not got_dirs:
        print_idx(idx, " ! No grabs performed!")
        write_to_log("No grabs performed for: " + dep_name)


def get_target_dir(data: dict, dep_name: str, driver: str):
    return sg.configuration[C_DRIVERS][driver]["target-dir"].format(
        **data, **sg.configuration, dep_name=dep_name)


def recursive_dependencies(idx: str, target_dir: str, data: dict, dep_name: str):
    if 'dep' not in data:
        print_idx(idx, "No 'dep' key found for dep: " + dep_name +
                  " using this dep-name as default (" + sg.args.dep + ")")
        data['dep'] = sg.args.dep
    dep_files = glob.glob(os.path.join(
        target_dir, data['dep']), recursive=True)
    print_idx(idx, " - Found dep-config:", dep_files)

    if len(dep_files) <= 0:
        return

    new_dependencies = {}
    for dep_file in dep_files:
        new_dependencies = load_dependencies_config(dep_file, new_dependencies)

    install_dependencies(idx, new_dependencies)


def use_driver(idx: str, data: dict, dep_name: str, driver: str, url: str):
    # default no arguments
    if "args" not in data:
        data["args"] = ""
    driver_data = sg.configuration[C_DRIVERS][driver]
    command = driver_data["command"].format(
        **data, **sg.configuration, dep_name=dep_name)
    target_dir = get_target_dir(data, dep_name, driver)
    if os.path.isdir(target_dir) and driver_data["needs-delete"]:
        print_idx(idx, " - Target folder", target_dir,
                  "exists. Will be deleted as the driver needs this")
        shutil.rmtree(target_dir)
    print_idx(idx, " > Executing:", command)
    feedback = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    return_code = feedback.wait()
    write_proc_to_log(idx, feedback.stdout, False)
    if return_code != 0:
        print_idx(idx, " - Error-Log of Driver:")
    write_proc_to_log(idx, feedback.stderr, return_code != 0)

    if(sg.configuration[C_RECURSIVE]):
        recursive_dependencies(idx, target_dir, data, dep_name)

    if return_code != 0:
        print_idx(idx, " ! Driver failed with code", feedback, "exiting.")
        sys.exit(return_code)

    grab_stuff(idx, dep_name, target_dir, data)


def install_dependency(name: str, idx: str, data: dict):
    print_idx(idx, "Loading \"" + name + "\"")
    if "url" not in data:
        print_idx(idx, " ! The dependency did not have an url-tag attached")
    url = data["url"]
    print_idx(idx, " - Loading from: \"" + url + "\"")
    if "driver" not in data:
        if not sg.configuration[C_AUTODETECT_DRIVERS]:
            print_idx(idx, " ! No driver given and autodetection disabled!")
        else:
            data["driver"] = detect_driver(idx, url)
    driver = data["driver"]
    print_idx(idx, " - Using driver: \"" + driver + "\"")

    if name in loaded:
        print_idx(idx, " > Skipping retrieval", name,
                  " as it was already loaded by another dep.")
        grab_stuff(idx, name, get_target_dir(data, name, driver), data)
        return
    loaded.append(name)

    if driver not in sg.configuration[C_DRIVERS]:
        print_idx(idx, " ! The selected driver is unknown. Loaded:",
                  sg.configuration[C_DRIVERS])
        sys.exit(2)

    use_driver(idx, data, name, driver, url)


def install_dependencies(idx: int, dep_dict: dict, first: bool = False):
    with futures.ThreadPoolExecutor(max_workers=sg.args.threads) as pool:
        runners = []
        for i, dep in enumerate(dep_dict['dependencies']):
            runners.append(pool.submit(install_dependency, dep, str(
                i) if first else str(idx) + "." + str(i), dep_dict['dependencies'][dep]))
        futures.wait(runners)
        for runner in runners:
            if runner.result() is not None:
                print(runner.result())
