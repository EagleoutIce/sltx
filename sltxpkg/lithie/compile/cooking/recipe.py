import glob
import os
import random
import shutil
import tempfile
from os.path import abspath, basename, splitext
from typing import List

from importlib_resources import files

import sltxpkg.config as sc
import sltxpkg.commands as scmd
import sltxpkg.data.recipes
import sltxpkg.globals as sg
import sltxpkg.lithie.compile.cooking.recipe_exceptions as rex
import sltxpkg.lithie.compile.tools as tools
from sltxpkg.log_control import LOGGER
import sltxpkg.util as su
from sltxpkg.globals import print_idx
from sltxpkg.util import create_multiple_replacer

BRACE_REPLACER = create_multiple_replacer({
    ':braceo:': '{',
    ':bracee:': '}',
})


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
        'extra_args': [],
        'tools': [],
        # to retrieve files:
        'wanted_files': [],
        'executable': '',
        'run': [],
        'quiet': ''
    }

    quiet = ''

    def __init__(self, recipe_path: str, file: str, idx: str):
        super().__init__()
        self.file = file
        self.idx = idx
        recipe_full_path = recipe_path
        if not os.path.isfile(recipe_full_path):
            recipe_full_path = str(
                files(sltxpkg.data.recipes).joinpath(recipe_path))
        if not os.path.isfile(recipe_full_path):
            print_idx(self.idx, "Recipe " + recipe_full_path +
                      " was not found. Exiting.")
            exit(1)
        print_idx(self.idx, "Loading recipe: " + recipe_full_path)
        y_conf = su.load_yaml(recipe_full_path)
        self.settings = {**self.settings, **y_conf}
        if sg.args.quiet:
            self.quiet = self.settings['quiet']
        self.__process_tools()
        self.__sanitize_extra_args()  # we need them as a single string

    def __process_tools(self):
        for tool in self.settings['tools']:
            getattr(tools, 'tool_' + tool)(self)

    def __sanitize_extra_args(self):
        self.settings['extra_args'].extend(sg.args.extra_arguments)
        self.settings['extra_args'].extend(sg.configuration[sg.C_BASE_ARGS])
        self.settings['extra_args'] = " ".join(self.settings['extra_args'])

    @staticmethod
    def get_default_recipes() -> List[str]:
        return [f for f in os.listdir() if f.endswith(".recipe")]

    # format; TODO: maybe cache the results
    def __f(self, t: str) -> str:
        for _ in range(sg.configuration[sg.C_FORMAT_MAX]):
            t = t.format(**self.settings, **sg.configuration, file=self.file,
                         filenoext=splitext(self.file)[0], do_quiet=self.quiet,
                         file_base_noext=splitext(basename(self.file))[0],
                         tmp=tempfile.gettempdir(),
                         out_dir=os.path.join("{cache_dir}", su.sanitize_filename(abspath(self.file))))
        return BRACE_REPLACER(t)

    def __runcmds(self, cmds: List[str]):
        for cmd in cmds:
            cmd = self.__f(cmd)  # expand
            if sg.args.verbose:
                print_idx(self.idx, "  - " + cmd)
            os.system(cmd)

    def __runhooks(self, hookid: str):
        if sg.args.verbose:
            print_idx(self.idx, "> Hooks for \"" + hookid + "\"")
        self.__runcmds(self.settings['hooks'][hookid])

    def __critical_abort(self, code: int):
        print_idx(self.idx, "Collecting files in working directory")
        archive = shutil.make_archive(os.path.join(
            os.getcwd(), 'sltx-log-' + su.get_now() + '-' + su.sanitize_filename(self.file)), 'zip',
            self.__f("{out_dir}"))
        print_idx(self.idx, "  - Created: \"" + archive +
                  "\" (" + os.path.basename(archive) + ")")

        # We have to force latexmk into think it has to re-run
        # TODO: We should check if not aux but we do this
        # We do this as we need a change and the percent itself gets consumed
        # This ensures a different sequence every time that will be deleted
        # on a successful run
        if sg.configuration[sg.C_CLEAN_ON_FAILURE]:
            LOGGER.info('Running auto clean on failure.')
            sg.args.exclude_patterns = []
            sg.args.include_patterns = [self.__f("{out_dir}")]
            scmd.cleanse_caches()
        else:
            with open(self.__f("{out_dir}/{file_base_noext}.aux"), 'a') as f:
                f.write('%% sltx errormark' + str(random.random()) +
                        " - " + str(random.random()))
        # automatic analyze
        os.system('sltx analyze "' + archive + '"')
        raise rex.RecipeException(archive,
                                  'Recipe for ' + str(self.idx) + ' failed with code: ' + str(
                                      code) + '. See logfile: \"' + archive + "\"")

    def __save_files(self, our_dir: str):
        """Retrieves the resulting files by patterns

        Args:
            our_dir (str): the path to the target directory for caught files
        """
        print_idx(self.idx, '> Retrieving resulting files to "' + our_dir + '"')
        got_files = []
        for wf in self.settings['wanted_files'] + sg.configuration[sg.C_WANTED_FILES]:
            wf = self.__f(wf)
            if sg.args.verbose:
                print_idx(
                    self.idx, '  - Retrieving files for pattern "' + wf + '"')
            wanted = glob.glob(os.path.join(
                sg.configuration[sg.C_WORKING_DIR], wf))
            for f in wanted:
                if sg.args.verbose:
                    print_idx(self.idx, "Saving \"" + f + "\" ")
                shutil.copy2(f, our_dir)
            got_files += wanted

        if not sg.args.verbose:
            print_idx(self.idx, "Saved files (" + str(got_files) + ")")

    def run(self):
        """Executes the configured Recipe
        """
        print_idx(self.idx, "Processing file: " + self.file, pre='\n')
        sc.assure_dirs()  # Ensure Working diSr and texmf home
        sc.assure_dir('file cache', self.__f("{out_dir}"), True)
        print_idx(self.idx, self.__f(
            "> Running recipe \"{name}\" by \"{author}\"."))
        self.__runhooks('pre')

        print_idx(self.idx, "> Running the compile commands (" +
                  str(len(self.settings['run'])) + ")")
        for i, cmd in enumerate(self.settings['run']):
            cmd = self.__f(cmd)  # expand
            if sg.args.verbose:
                print_idx(self.idx, "  - " + cmd)
            fback = os.system(cmd)
            if fback != 0:
                print_idx(self.idx,
                          "\033[31m  ! The command failed. Initiating critical abort...\033[m")
                self.__critical_abort(fback)

        self.__runhooks('in')
        self.__save_files(os.getcwd())
        self.__runhooks('post')
        if sg.configuration[sg.C_CLEANUP]:
            print_idx(self.idx, "> Cleaning up (configured by configuration)")
            self.__runcmds(self.settings['cleanup_cmds'])
