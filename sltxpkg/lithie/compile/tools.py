import sltxpkg.lithie.compile.latexmk_mos as lmos
from sltxpkg import globals as sg
from sltxpkg.globals import LOGGER


def tool_glossary(recipe):
    if sg.args.verbose:
        LOGGER.info("Tool: Glossary")
    lmos.append_local2global_config('glossary')


def tool_index(recipe):
    if sg.args.verbose:
        LOGGER.info("Tool: index")
    lmos.append_local2global_config('index')
