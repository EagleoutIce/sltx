import glob
import os
import re
import shutil
import sys
from concurrent import futures
from subprocess import PIPE, Popen  # execution
from pathlib import Path

import sltxpkg.globals as sg
from sltxpkg.config import load_dependencies_config, write_to_log
from sltxpkg.globals import (C_AUTODETECT_DRIVERS, C_CLEANUP, C_CREATE_DIRS,
							 C_DRIVER_LOG, C_DRIVER_PATTERNS, C_DRIVERS,
							 C_RECURSIVE, C_TEX_HOME, C_DOWNLOAD_DIR,
							 DEFAULT_CONFIG, print_idx)
import sltxpkg.util as su
from sltxpkg import dep

loaded = []


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


def write_proc_to_log(idx: int, stream, mirror: bool):
	while True:
		line = stream.readline()
		if not line:
			break
		line_utf8 = line.decode('utf-8')
		write_to_log(line_utf8)
		if mirror:
			print_idx(idx, line_utf8)


def grab_stuff(idx: str, dep_name: str, target_dir: str, data: dict, target: str):
	print_idx(idx, " > Grabbing dependencies for " + dep_name)
	print_idx(idx, "   - Grabby-Grab-Grab files from \"" + target_dir + "\"...")
	got_files = grab_from(idx, target_dir, data, target,
						  'grab-files', f_grab_files)
	print_idx(idx, " - Grabby-Grab-Grab dirs from \"" + target_dir + "\"...")
	got_dirs = grab_from(idx, target_dir, data, target,
						 'grab-dirs', f_grab_dirs)
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
	print_idx(idx, " - Found dep-config:", dep_files)

	if len(dep_files) <= 0:
		return

	new_dependencies = {}
	for dep_file in dep_files:
		new_dependencies = load_dependencies_config(dep_file, new_dependencies)

	_install_dependencies(idx, new_dependencies, target)


def use_driver(idx: str, data: dict, dep_name: str, driver: str, url: str, target: str):
	# default no arguments
	if "args" not in data:
		data["args"] = ""
	driver_data = sg.configuration[C_DRIVERS][driver]
	command = driver_data["command"].format(
		**data, **sg.configuration, dep_name=dep_name)
	driver_target_dir = get_target_dir(data, dep_name, driver)
	if os.path.isdir(driver_target_dir) and driver_data["needs-delete"]:
		print_idx(idx, " - Target folder", driver_target_dir,
				  "exists. Will be deleted as the driver needs this")
		shutil.rmtree(driver_target_dir)
	print_idx(idx, " > Executing:", command)
	feedback = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
	return_code = feedback.wait()
	write_proc_to_log(idx, feedback.stdout, False)
	if return_code != 0:
		print_idx(idx, " - Error-Log of Driver:")
	write_proc_to_log(idx, feedback.stderr, return_code != 0)

	if(sg.configuration[C_RECURSIVE]):
		recursive_dependencies(idx, driver_target_dir, data, dep_name, target)

	if return_code != 0:
		print_idx(idx, " ! Driver failed with code", feedback, "exiting.")
		sys.exit(return_code)

	grab_stuff(idx, dep_name, driver_target_dir, data, target)


def install_dependency(name: str, idx: str, data: dict, target: str):
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
		grab_stuff(idx, name, get_target_dir(data, name, driver), data, target)
		return
	loaded.append(name)

	if driver not in sg.configuration[C_DRIVERS]:
		print_idx(idx, " ! The selected driver is unknown. Loaded:",
				  sg.configuration[C_DRIVERS])
		sys.exit(2)

	use_driver(idx, data, name, driver, url, target)


def _install_dependencies(idx: int, dep_dict: dict, target: str, first: bool = False):
	with futures.ThreadPoolExecutor(max_workers=sg.args.threads) as pool:
		runners = []
		for i, dep in enumerate(dep_dict['dependencies']):
			runners.append(pool.submit(install_dependency, dep, str(
				i) if first else str(idx) + "." + str(i), dep_dict['dependencies'][dep], target))
		futures.wait(runners)
		for runner in runners:
			if runner.result() is not None:
				print(runner.result())


def install_dependencies(target: str = su.get_sltx_tex_home()):
	if "target" not in sg.dependencies or "dependencies" not in sg.dependencies:
		print("The dependency-file must supply a 'target' and an 'dependencies' key!")
		sys.exit(1)

	write_to_log("====Dependencies for:" + sg.dependencies["target"]+"\n")
	print()
	print("Dependencies for:", sg.dependencies["target"])
	print("Installing to:", target)
	print()

	_install_dependencies(0, sg.dependencies, target, first=True)

	# all installed
	if sg.configuration[C_CLEANUP]:
		print("> Cleaning up the download directory, as set.")
		shutil.rmtree(sg.configuration[C_DOWNLOAD_DIR])
	print("Loaded:", dep.loaded)
	if not sg.configuration[C_RECURSIVE]:
		print("Recursion was disabled.")
	print("Dependency installation for",
		  sg.dependencies["target"], "completed.")
