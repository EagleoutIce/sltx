from importlib_resources import files
import sltxpkg.data.recipes
import os
import yaml

import sltxpkg.lithie.compile.tools as tools
import sltxpkg.util as su


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
        'executable': 'latexmk',
        'run': ['{executable} {args} {eargs} {file}']
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

    def __process_tools(self):
        for tool in self.settings['tools']:
            getattr(tools, 'tool_' + tool)(self)

    @staticmethod
    def get_default_recipes() -> [str]:
        print([f for f in os.listdir() if f.endswith(".recipe")])
        pass
