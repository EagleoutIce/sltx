import os  # list directory
import re
import shutil  # clean working dir
from pathlib import Path

from importlib_resources import files

import sltxpkg.data
import sltxpkg.lithie.compile.cooker as cooker
from sltxpkg import generate, util as su, config as sc, globals as sg
from sltxpkg.config import (assure_dirs, load_dependencies_config)
from sltxpkg.dep import install_dependencies
from sltxpkg.globals import (C_USE_DOCKER,
                             C_DOCKER_PROFILE)
from sltxpkg.lithie import commands as lithiecmd
from sltxpkg.lithie.analyze.analyzer import Analyzer
from sltxpkg.log_control import LOGGER


def cmd_auto_setup():
    sc.assure_dirs()
    cleanse_caches()

    if sg.args.auto_deps:
        dep_path = str(files(sltxpkg.data).joinpath('sltx-dep.yaml'))
        sg.dependencies = load_dependencies_config(dep_path, sg.dependencies)
        install_dependencies()

    # TODO: allow option to install local dependencies too using the shipped sltx-dep?
    lithiecmd.install(sg.configuration[sg.C_DOCKER_PROFILE])


def cmd_dependency():
    if sg.args.deps is None or len(sg.args.deps) == 0:
        LOGGER.error("You must supply a dependency 'file'.")
        exit(1)

    for dep in sg.args.deps:
        # will extend the dict with 'new' ones
        # should work even better if sltx-source.yaml files are present in the targets
        sg.dependencies = load_dependencies_config(dep, sg.dependencies)

    assure_dirs()

    target = su.get_sltx_tex_home() if sg.args.local_path is None else sg.args.local_path
    install_dependencies(target=target)


def cmd_version():
    LOGGER.info("This is sltx, a simple latex helper-utility")
    LOGGER.info("Tex-Home: " + su.get_tex_home())
    LOGGER.info("Default config location: %s (present: %s)",
                su.get_default_conf(), str(os.path.isfile(su.get_default_conf())))
    LOGGER.info("Local config location: %s (present: %s)",
                su.get_local_conf(), str(os.path.isfile(su.get_local_conf())))
    LOGGER.info("Version: " + su.get_version())


def cmd_docker():
    lithiecmd.install_ask_user()


def cmd_raw_compile():
    # install possible deps
    for dep in sg.args.extra_dependencies:
        # will extend the dict with 'new' ones
        # should work even better if sltx-source.yaml files are present in the targets
        sg.dependencies = load_dependencies_config(dep, sg.dependencies)
    # i know just writing without len is more pythonic but i like it more if it is explicit
    if len(sg.args.extra_dependencies) > 0:
        texmf_home = su.get_tex_home()
        LOGGER.info("Insalling additional dependencies.")
        assure_dirs()
        install_dependencies(target=texmf_home)

    cooker.cook()
    # if no exception we went here compiling fine
    if sg.configuration[sg.C_CLEANUP]:
        sg.args.exclude_patterns = []
        sg.args.cleanse_all = False
        sg.args.cleanse_cache = False
        cmd_cleanse()


def cmd_compile():
    if sg.configuration[C_USE_DOCKER]:
        LOGGER.info("Using docker to compile (" +
                    sg.configuration[C_DOCKER_PROFILE] + ")")
        lithiecmd.compile()
    else:
        LOGGER.info("Docker was disabled, using local compilation.")
        cmd_raw_compile()


def cmd_gen_gha():
    generate.generate()


def should_be_excluded(file: str):
    if vars(sg.args).get('exclude_patterns') is None:
        return False

    for exclude_pattern in sg.args.exclude_patterns:
        if re.match(exclude_pattern, file):
            return True
    return False


def should_be_included(file: str):
    if vars(sg.args).get('include_patterns') is None:
        return True

    for include_pattern in sg.args.include_patterns:
        if re.match(include_pattern, file):
            return True
    return False


def cleanse_caches():
    # TODO: clean up .latexmkrc entries; not the whole file
    cache_dir = sg.configuration[sg.C_CACHE_DIR]
    if os.path.isdir(cache_dir):
        LOGGER.info("Cleaning all the caches... (" + cache_dir + ")")
        # avoids deleting the cache dir itself
        for root, folder_dirs, folder_files in os.walk(cache_dir):
            for name in folder_files:
                f = os.path.join(root, name)
                if not should_be_excluded(str(f)) and should_be_included(str(f)):
                    os.remove(f)
            for name in folder_dirs:
                f = os.path.join(root, name)
                if not should_be_excluded(str(f)) and should_be_included(str(f)):
                    shutil.rmtree(os.path.join(root, name))
    else:
        LOGGER.warning("No caches \"" + cache_dir +
                       "\" were found. Skipping...")


def cmd_analyze_logfile():
    for i, file in enumerate(sg.args.files):
        analyzer = Analyzer(file, i)
        analyzer.analyze()


def cmd_cleanse():
    sc.assure_dirs()
    # Delete all current log files
    # TODO: make this dry. avoid specifying the log files signature multiple times (see Recipe)
    LOGGER.info("Cleaning local logs...")
    clean_patterns = ['sltx-log-*.tar.gz',
                      'sltx-log-*.zip', 'sltx-drivers.log', '*.sltx-log']
    for clean_pattern in clean_patterns:
        for f in Path(".").glob(clean_pattern):
            if should_be_excluded(str(f)) or not should_be_included(str(f)):
                LOGGER.info("File " + str(f) + " excluded.")
            else:
                f.unlink()
    if sg.args.cleanse_all:
        texmf_home = su.get_sltx_tex_home()
        if os.path.isdir(texmf_home):
            LOGGER.error("Cleaning sltx-texmf-tree... (" + texmf_home + ")")
            shutil.rmtree(texmf_home)
        else:
            LOGGER.warning("The local sltx-texmf tree in \"" +
                           texmf_home + "\" was not found. Skipping...")

    if sg.args.cleanse_all or sg.args.cleanse_cache:
        cleanse_caches()
