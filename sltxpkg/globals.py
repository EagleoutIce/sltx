import sys

DEFAULT_CONFIG = "~/.sltx-config.yml"
LOCAL_CONFIG = "./sltx-config.yml"

DEFAULT_DEPENDENCY="sltx-dep.yml"

C_DRIVER_LOG = "driver_log"
C_TEX_HOME = "tex_home"
C_WORKING_DIR = "working_dir"
C_CREATE_DIRS = "create_dirs"
C_CLEANUP = "cleanup"
C_AUTODETECT_DRIVERS = "autodetect_drivers"
C_DRIVERS = "drivers"
C_DRIVER_PATTERNS = "driver_patterns"
C_RECURSIVE = "recursive"
C_FORMAT_MAX = "format_max"
C_INCLUDE_LOCAL_TEXMF = "include_local_texmf"
C_DOWNLOAD_DIR = 'download_dir'
C_CACHE_DIR = 'cache_dir'
# Use for auto-file
C_DEFAULT_FILES = 'default_files'
C_DEFAULT_THREADS = 'default_threads'
C_DEFAULT_RECIPE = 'default_recipe'
C_WANTED_FILES = 'extra_wanted_files'

C_USE_DOCKER = "docker_use"
C_DOCKER_PROFILE = "docker_profile"

DOCKER_URL = "eagleoutice/lithie-{profile}"

configuration = {
	C_TEX_HOME: "{os_default_texmf}/tex/latex/sltx",
	C_WORKING_DIR: "~/.sltx",
	C_DOWNLOAD_DIR: "~/.sltx/download",
	C_CACHE_DIR: "~/.sltx/cache",
	C_DEFAULT_FILES: [],
	C_DEFAULT_RECIPE: "default-latexmk.recipe",
	C_DRIVER_LOG: "sltx-drivers.log",
	C_DEFAULT_THREADS: 1,
	C_CREATE_DIRS: True,
	C_CLEANUP: True,
	C_RECURSIVE: True,
	C_INCLUDE_LOCAL_TEXMF: False,
	C_FORMAT_MAX: 5, # Max formatting depth
	C_USE_DOCKER: True,
	C_DOCKER_PROFILE: 'tx-default',
	C_WANTED_FILES: [],
	C_AUTODETECT_DRIVERS: True,
	# TODO maybe specific install routine instead of plain copy
	C_DRIVERS: {
		"git": {
			"command": "git clone --depth 1 {args} \"{url}\" \"{download_dir}/{dep_name}\"",
			"target-dir": "{download_dir}/{dep_name}",
			"needs-delete": True  # if already exists
			# TODO: maybe update routine?
		}
		# TODO: others
	},
	C_DRIVER_PATTERNS: {
		"git": ["github", "gitlab"]
	}
}

dependencies = {}

def print_idx(idx : int, *objects, sep=' ', end='\n',pre='', file=sys.stdout, flush=False):
	print(pre,"[ID " + str(idx) + "]", *objects, sep=sep, end=end, file=file, flush=flush)

# global arguments read in
args = None