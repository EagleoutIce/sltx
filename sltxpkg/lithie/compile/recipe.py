
class Recipe():
    
    settings = {
        'name': 'Default recipe (latexmk!)',
        'author': 'Florian Sihler',
        'use-cases': [],
        'hooks': {
            'pre': [],
            'post': []
        },
        # Will add a hook to cleanup files
        'cleanup': True,
        'args': '-pdf -file-line-error -halt-on-error -interaction=nonstopmode -outdir {working_dir}',
        'eargs': ['-f'], # extra args
        # Tools will be used to generate files if needed or to require intermediate steps
        # They extend the hooks and can use ifs
        # They will extend eargs as well (bib for example will add -bibtex?)
        'tools': ['bibliography', 'glossary', 'index'],
        'variables': {
            # Variables will be used for expansion in other strings
            'working_dir': '{tmp}/sltx/compile',
            'filter': '{file}.pdf'
        },
        # TODO: latexmk pretex
        # TODO latexmkrc if no ile is needd?
        'command': 'latexmk {args} {eargs} {file}'
    }

    def __init__(self):
        super().__init__()
        eval(self.settings['pre'])
