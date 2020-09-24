import sltxpkg.lithie.compile.latexmk_mos as lmos

def tool_glossary(recipe):
    print("Tool: Glossary")
    # Config for latexmk
    lmos.append_local2global_config('glossary')
