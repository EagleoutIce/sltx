import argparse
import os

import sltxpkg.util as su
from sltxpkg.command_config import Arg, Commands
from sltxpkg.commands import (cmd_analyze_logfile, cmd_auto_setup, cmd_cleanse,
                              cmd_compile, cmd_dependency, cmd_docker,
                              cmd_gen_gha, cmd_raw_compile, cmd_version)


def valid_file(arg: str) -> str:
    if arg is None or arg.strip() == "":
        raise ValueError("arg vas none or empty")
    if not os.path.isfile(arg):
        raise FileNotFoundError("\"" + arg + "\" must be an existing file")
    return arg


file_help = "the file(s) to load; they will be processed."
file_tx = "file.tex"

sub_parser = Commands({
    'analyze': ((cmd_analyze_logfile, ['log']),
                Arg(description='Analyze a logfile for errors.'),
                [
                    Arg('files', metavar='log.zip',
                        type=str, nargs='*', help=file_help)]
                ),
    'dependency': ((cmd_dependency, ['dep']),
                   Arg(description='Install dependencies on the host system.'),
                   [
                       Arg('-l', '--local', metavar='path', dest='local_path', default=None,
                           help="This will install the dependency file into the given directory. This might be useful "
                                "if the compilation should be handled by an online editor. Use '.' to use the current "
                                "directory."),
                       Arg('deps', metavar='dep.yml', type=valid_file, nargs='+',
                           help="the file(s) to load the dependencies from.")
    ]),
    'docker': ((cmd_docker, ['do']), Arg(description='Manage the containers to compile with sltx.'), []),
    'compile': ((cmd_compile, ['cmp']), Arg(
        description="Compile documents with previously installed containers. If docker was disabled this will default "
                    "to the same behavior as \"raw-compile\" passing on the recipe."),
                [
                    Arg('-p', '--profile', dest='profile',
                        help="allows to override the configured docker profile. This will enable docker automatically."),
                    Arg('-r', '--recipe', dest='recipe',
                        help='The recipe to instruct the main compile routine.', required=False, default=None),
                    Arg('--root', dest='dock_as_root', action='store_true',
                        help='Run the docker container with the lithie-root setup. This may lead to permission errors '
                             'when you want to delete the caches.',
                        required=False),
                    Arg('-l', '--local-texmf', dest='local_texmf', action='store_true', default=False,
                        help='include the local texmf tree in the docker container', required=False),
                    Arg('--no-local-texmf', dest='local_texmf', action='store_false',
                        help='exclude the local texmf tree in the docker container', required=False),
                    Arg('-d', '--dependencies', dest='extra_dependencies', action='append', default=[],
                        help='additional dependency files to download before the installation. May be supplied '
                             'multiple times.',
                        required=False),
                    Arg('-a', '--args', action='append', metavar='ARGUMENT(S)', dest='extra_arguments', default=[],
                        help="Extra arguments. Make sure to prepend them with the appropriate '-' or '--', they will "
                             "be used as extra_arguments in the recipe."),
                    Arg('files', metavar=file_tx, type=str, nargs='*',
                        help=file_help)
    ]),
    'raw-compile': ((cmd_raw_compile, ['raw-cmp']), Arg(
        description="Compile documents using a recipe. This will not start any docker container but will be executed "
                    "inside one as well."),
                    [
                        Arg('-r', '--recipe', dest='recipe',
                            help='The recipe to instruct the main compile routine.', required=False, default=None),
                        Arg('files', metavar=file_tx, type=str, nargs='*',
                            help=file_help),
                        Arg('-a', '--args', action='append', metavar='ARGUMENT(S)', dest='extra_arguments', default=[],
                            help="Extra arguments. Make sure to prepend them with the appropriate '-' or '--', "
                                 "they will be used as extra_arguments in the recipe."),
                        Arg('-d', '--dependency', dest='extra_dependencies', action='append', default=[],
                            help='additional dependency files to download before the installation. May be supplied '
                                 'multiple times.',
                            required=False)
    ]),
    'gen-gha': ((cmd_gen_gha, ['gha']), Arg(description='Generate a GitHub workflow To automate compilation.'), []),
    'cleanse': ((cmd_cleanse, ['cls']), Arg(
        description="This will clean all additional sltx-files in the current directory (like \"sltx-log-*\" files). "
                    "It may clean more, if you pass the corresponding flags. Please note, that cleanse will only read "
                    "the current config. If you've changed some configurations they will be used."),
                [
                    Arg('-C', '--cache', dest='cleanse_cache', action='store_true',
                        help="If set, sltx will clean the caches."),
                    Arg('--all', dest='cleanse_all', action='store_true',
                        help="If set, sltx will clean the texmf-tree (sltx) and the complete cache as-well."),
                    Arg('-e', '--exclude', action='append', metavar='pattern', dest='exclude_patterns',
                        help="Exclude all files/directories matching this pattern. May be supplied multiple times."),
                    Arg('-i', '--include', action='append', metavar='pattern', dest='include_patterns',
                        help="Include *only* files/directories matching this pattern. May be supplied multiple times.")
    ]),
    'auto-setup': (
        (cmd_auto_setup, []), Arg(
            description='Setup a basic version of sltx (this requires docker to be setup).'),
        [
            Arg('-d', '--dependencies', dest='auto_deps', action='store_true',
                help='This will install the recommended dependencies on your host system. This is helpful if you have '
                'texlive installed and want your editor to recognize the libraries as well.')
        ]),
    'version': ((cmd_version, []), Arg(description='Show the version-info for sltx.'), [])
})

parser = argparse.ArgumentParser(
    description="sltx, a Simple LaTeX utility", epilog="sltx Version: " + su.get_version())

# commands, parser.add_mutually_exclusive_group()
parser.add_argument('-c', '--config', dest='config', metavar='config.yml',
                    required=False, type=valid_file,
                    help="the file to load the configuration from.")

parser.add_argument('-t', '--threads', metavar='N', dest='threads', type=int,
                    help="number of threads to run the installation. Default is 1. This number will only affect some "
                         "routines.",
                    default=-1)

parser.add_argument('-q', '--quiet', dest='quiet',
                    required=False, action='store_true',
                    help="Set the flag if output is to be reduced")

parser.add_argument('-v', '--verbose', dest='verbose',
                    required=False, action='store_true',
                    help="Output in verbose mode -> more information from sltx")

parser.add_argument('--log', dest='log',
                    required=False, action='store_true',
                    help="Write to logfile. This is experimental.")

# TODO: Format support with mlatexformat?
cmd_parser = parser.add_subparsers(title='command', description="Select the command for sltx", metavar=set(sub_parser.cmds.keys()),
                                   help="Help for the specific command. You may use shortcuts for them: " +
                                   str([k[1] for k in sub_parser.helper_values() if len(
                                       k[1]) != 0]),
                                   dest='command')

sub_parser.generate(cmd_parser)
