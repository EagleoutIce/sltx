import sys

DEFAULT_CONFIG = "./sltx-config.yml"
C_DRIVER_LOG = "driver_log"
C_TEX_HOME = "tex_home"
C_WORKING_DIR = "working_dir"
C_CREATE_DIRS = "create_dirs"
C_CLEANUP = "cleanup"
C_AUTODETECT_DRIVERS = "autodetect_drivers"
C_DRIVERS = "drivers"
C_DRIVER_PATTERNS = "driver_patterns"
C_RECURSIVE = "recursive"

configuration = {
    C_TEX_HOME: "~/texmf/tex/latex/sltxinst",
    C_WORKING_DIR: "~/.sltxinst",
    C_DRIVER_LOG: "sltx-drivers.log",
    C_CREATE_DIRS: True,
    C_CLEANUP: True,
    C_RECURSIVE: True,
    C_AUTODETECT_DRIVERS: True,
    # TODO maybe specific install routine instead of plain copy
    C_DRIVERS: {
        "git": {
            "command": "git clone --depth 1 {args} \"{url}\" \"{working_dir}/{dep_name}\"",
            "target-dir": "{working_dir}/{dep_name}",
            "needs-delete": True  # if already exists
            # TODO: maybe update routine?
        }
        # TODO: other
    },
    C_DRIVER_PATTERNS: {
        "git": ["github", "gitlab"]
    }
}

dependencies = {}

def print_idx(idx : int, *objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    print("[ID " + str(idx) + "]", *objects, sep=sep, end=end, file=file, flush=flush)

# global arguments read in
args = None