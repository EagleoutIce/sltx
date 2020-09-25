import glob
import os
import shutil
import tempfile

import sltxpkg.config as sc
import sltxpkg.data.recipes
import sltxpkg.globals as sg
import sltxpkg.lithie.compile.tools as tools
import sltxpkg.util as su
import yaml
from importlib_resources import files

# TODO: in case of error pack the directory with tar and ship it to the folder
# TODO: show the log dump (like jake)


class Recipe():

    settings = {
        'name': '',
        'author': '',
        'hooks': {
            'pre': [],
            'in': [],  # before retrieval
            'post': []  # before cleanup
        },
        # cleanup will be determined by global settings
        'cleanup_cmds': [],
        'args': '',
        'eargs': [],
        'tools': [],
        # to retrieve files:
        'wanted_files': [],
        'executable': '',
        'run': []
    }

    def __init__(self, recipe_path: str):
        super().__init__()
        recipe_full_path = recipe_path
        if not os.path.isfile(recipe_full_path):
            recipe_full_path = str(
                files(sltxpkg.data.recipes).joinpath(recipe_path))
        if not os.path.isfile(recipe_full_path):
            print("Recipe", recipe_full_path, "was not found. Exiting.")
            exit(1)
        print("Loading recipe:", recipe_full_path)
        y_conf = su.load_yaml(recipe_full_path)
        self.settings = {**self.settings, **y_conf}
        self.__process_tools()
        self.__sanitize_eargs()  # we need them as a single string

    def __process_tools(self):
        for tool in self.settings['tools']:
            getattr(tools, 'tool_' + tool)(self)

    def __sanitize_eargs(self):
        self.settings['eargs'] = " ".join(self.settings['eargs'])

    @staticmethod
    def get_default_recipes() -> [str]:
        return [f for f in os.listdir() if f.endswith(".recipe")]

    # format
    def __f(self, t: str) -> str:
        for _ in range(sg.configuration[sg.C_FORMAT_MAX]):
            t = t.format(**self.settings, **sg.configuration, file=sg.args.file,
                         filenoext=os.path.splitext(sg.args.file)[0],
                         tmp=tempfile.gettempdir(),
                         out_dir=os.path.join("{cache_dir}", su.sanitize_filename(os.path.abspath(sg.args.file))))
        return t

    def __runcmds(self, cmds: [str]):
        for cmd in cmds:
            cmd = self.__f(cmd)  # expand
            print("  -", cmd)
            os.system(cmd)

    def __runhooks(self, hookid: str):
        print("> Hooks for \"" + hookid + "\"")
        self.__runcmds(self.settings['hooks'][hookid])

    def __critical_abort(self, code: int):
        print("Collecting files in working directory")
        archive = shutil.make_archive(os.path.join(os.getcwd(
        ), 'sltx-log-' + su.get_now()), 'gztar', sg.configuration[sg.C_WORKING_DIR])
        print("  - Created: \"" + archive +
              "\" (" + os.path.basename(archive) + ")")
        exit(code)

    # Run the recipe
    def run(self):
        sc.assure_dirs()  # Ensure Working diSr and texmf home
        print(self.__f("> Running recipe \"{name}\" by \"{author}\"."))
        self.__runhooks('pre')

        print("> Running the compile commands")
        for cmd in self.settings['run']:
            cmd = self.__f(cmd)  # expand
            print("  -", cmd)
            fback = os.system(cmd)
            if fback != 0:
                print(
                    "\033[31m  ! The command failed. Initiating critical abort...\033[m")
                self.__critical_abort(fback)

        self.__runhooks('in')

        our_dir = os.getcwd()

        # Get the resulting file(s)
        print("> Retrieving resulting files to \"" + our_dir + "\"")
        for wf in self.settings['wanted_files']:
            wf = self.__f(wf)
            print("  - Retrieving files for pattern \"" + wf + "\"")
            wanted = glob.glob(os.path.join(
                sg.configuration[sg.C_WORKING_DIR], wf))
            for f in wanted:
                print("Saving \"" + f + "\" ")
                shutil.copy(f, our_dir)

        self.__runhooks('post')
        if sg.configuration['cleanup']:
            print("> Cleaning up (configured by configuration)")
            self.__runcmds(self.settings['cleanup_cmds'])
