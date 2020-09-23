
class Recipe():
    
    settings = {
        'name': '',
        'author': '',
        'use-cases': [],
        'hooks': {
            'pre': [],
            'post': []
        },
        'cleanup': True,
        'args': '',
        'eargs': [],
        'tools': [],
        'variables': {
            'working_dir': '{tmp}/sltx/compile',
            'filter': '{file}.pdf'
        },
        'command': 'latexmk {args} {eargs} {file}'
    }

    def __init__(self, recipe_path : str):
        super().__init__()
        eval(self.settings['pre'])


    @staticmethod
    def get_default_recipes() -> [str]:
        RECIPE_PATH = pkg_resources.resource_dir('')
        pass # return [f for f in listdir()]