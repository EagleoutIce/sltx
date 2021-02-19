from importlib_resources import files, as_file
from sys import platform
import os
import sltxpkg.data.latexmk.configs
import sltxpkg.util as su

# We have to configure latexmk configuration-files os-dependent
# NOTE: no cygwin support

def get_root() -> str:
	if platform == "linux":
		return os.path.expandvars("$HOME/.latexmkrc")
	elif platform == "darwin":
		return os.path.expandvars("$HOME/.latexmkrc")
	elif platform == "win32":
		return "C:\latexmk\LatexMk"

def get_config(name : str) -> str:
	return files(sltxpkg.data.latexmk.configs).joinpath(name + '.mkrc').read_text()


def append_local2global_config(name : str):
	append_to_global_config(get_config(name), name)

# TODO: what if nonglobal? what if more deps?
def append_to_global_config(text : str, guard : str):
	file = get_root()
	START_GUARD = "# sltx START " + guard
	mode = 'a'

	if os.path.isfile(file) and su.file_contains(file, START_GUARD):
			print("Global latexmk config already contains config for",guard + ". Skipping.")
			return

	with open(file, mode) as f:
		f.write("\n" + START_GUARD + "\n")
		f.writelines(text)
		f.write("# sltx END " + guard + "\n")