import sltxpkg.lithie.compile.latexmk_mos as lmos

# Configs for latexmk

def tool_glossary(recipe):
	print("Tool: Glossary")
	lmos.append_local2global_config('glossary')

def tool_index(recipe):
	print("Tool: index")
	lmos.append_local2global_config('index')