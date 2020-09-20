import glob
import os
import shutil
import sys
from subprocess import Popen, PIPE  # execution
import re

from sltx_config import write_to_log
from sltx_globals import DEFAULT_CONFIG, C_DRIVER_LOG, C_TEX_HOME, C_WORKING_DIR, C_CREATE_DIRS, C_CLEANUP, C_AUTODETECT_DRIVERS, C_DRIVERS, C_DRIVER_PATTERNS
import sltx_globals as sg
from sltx_globals import print_idx

loaded = []


def detect_driver(idx: int, url: str):
    print_idx(idx, " - Autodetecting driver...")
    for key, patterns in sg.configuration[C_DRIVER_PATTERNS].items():
        for pattern in patterns:
            if re.search(pattern, url):
                return key
    print_idx(idx, " ! No driver found...")
    sys.exit(1)


def grab_files_from(idx: int, path: str, data: dict):
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


def grab_dirs_from(idx: int, path: str, data: dict):
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
        shutil.copytree(dir, os.path.join(
            sg.configuration[C_TEX_HOME], os.path.relpath(dir, path)))

    return True


def write_proc_to_log(stream):
    while True:
        line = stream.readline()
        if not line:
            break
        write_to_log(line.decode('utf-8'))

def grab_stuff(idx: int, dep_name: str, target_dir: str, data: dict):
    print_idx(idx, "Grabbing dependencies for " + dep_name)
    got_files = grab_files_from(idx, target_dir, data)
    got_dirs = grab_dirs_from(idx, target_dir, data)
    if not got_files and not got_dirs:
        print_idx(idx, " ! No grabs performed!")
        write_to_log("No grabs performed for: " + dep_name)

def get_target_dir(data: dict, dep_name: str, driver: str):
    return sg.configuration[C_DRIVERS][driver]["target-dir"].format(
        **data, **sg.configuration, dep_name=dep_name)

def use_driver(idx: int, data: dict, dep_name: str, driver: str, url: str):
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
    write_proc_to_log(feedback.stdout)
    write_proc_to_log(feedback.stderr)

    if return_code != 0:
        print_idx(idx, " ! Driver failed with code", feedback, "exiting.")
        sys.exit(return_code)

    grab_stuff(data, dep_name, target_dir, data)


def install_dependency(name: str, idx : int):
    print_idx(idx, "Loading \"" + name + "\"")
    data = sg.dependencies["dependencies"][name]
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
        print_idx(idx, "Skipping retrieval", name, " as it was already loaded by another dep.")
        grab_stuff(idx, name, get_target_dir(data, name, driver), data)
        return

    if driver not in sg.configuration[C_DRIVERS]:
        print_idx(idx, " ! The selected driver is unknown. Loaded:",
              sg.configuration[C_DRIVERS])
        sys.exit(2)
    use_driver(idx, data, name, driver, url)
    loaded.append(name)
