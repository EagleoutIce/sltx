import sltxpkg.lithie.compile.latexmk_mos as lmos
from sltxpkg.globals import LOGGER

# Configs for latexmk


def tool_glossary(recipe):
    LOGGER.info("Tool: Glossary")
    lmos.append_local2global_config('glossary')


def tool_index(recipe):
    LOGGER.info("Tool: index")
    lmos.append_local2global_config('index')
