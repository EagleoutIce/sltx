import os  # list directory
import shutil  # clean working dir
import sys

import sltxpkg.util as su
from sltxpkg import dep, generate, globals as sg
from sltxpkg.config import (assure_dirs, load_configuration,
                            load_dependencies_config, write_to_log)
from sltxpkg.dep import install_dependencies
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_CREATE_DIRS,
                             C_DRIVER_LOG, C_DRIVER_PATTERNS, C_DRIVERS,
                             C_TEX_HOME, C_WORKING_DIR, DEFAULT_CONFIG, C_RECURSIVE, C_USE_DOCKER)
import sltxpkg.lithie.compile.cooker as cooker

from sltxpkg.lithie import commands as lithiecmd

from concurrent import futures


def cmd_dependency():
    if sg.args.dep is None or sg.args.dep == "":
        print("You must supply a dependency 'file'.")
        exit(1)

    if os.path.isfile(DEFAULT_CONFIG):
        print("Automatically loading '{DEFAULT_CONFIG}'".format(
            **locals(), **globals()))
        load_configuration(DEFAULT_CONFIG)

    if sg.args.config is not None:
        load_configuration(sg.args.config)
    if sg.args.dep is not None:
        sg.dependencies = load_dependencies_config(
            sg.args.dep, sg.dependencies)

    assure_dirs()

    if "target" not in sg.dependencies or "dependencies" not in sg.dependencies:
        print("The dependency-file must supply a 'target' and an 'dependencies' key!")
        sys.exit(1)

    write_to_log("====Dependencies for:" + sg.dependencies["target"]+"\n")
    print()
    print("Dependencies for:", sg.dependencies["target"])
    print("Installing to:", sg.configuration[C_TEX_HOME])
    print()

    install_dependencies(0, sg.dependencies, first=True)

    # all installed
    if sg.configuration[C_CLEANUP]:
        print("> Cleaning up the working directory, as set.")
        shutil.rmtree(sg.configuration[C_WORKING_DIR])
    print("Loaded:", dep.loaded)
    if not sg.configuration[C_RECURSIVE]:
        print("Recursion was disabled.")
    print("Dependency installation for",
          sg.dependencies["target"], "completed.")


def cmd_version():
    print("This is sltx, a simple latex helper-utility")
    print("Version: ", su.get_version())


def cmd_docker():
    lithiecmd.install()


def cmd_raw_compile():
    cooker.cook()

def cmd_compile():
    if(sg.configuration[C_USE_DOCKER]):
        print("Using docker to compile")
        lithiecmd.compile()
    else:
        print("Docker was disabled, using local compilation.")
        cmd_raw_compile()
        # TODO: cleanup afterwards to avoid pollution of other ns
        # TODO: compile in another dir to avoid pollution and only return files based on a filter to the main directory


def cmd_gen_gha():
    generate.generate()
