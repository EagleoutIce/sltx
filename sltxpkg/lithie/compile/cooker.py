# cookes the recipe :D

from sltxpkg.lithie.compile.recipe import Recipe
import sltxpkg.globals as sg

def cook():
    recipe = Recipe('default-latexmk.recipe' if sg.args.recipe is None else sg.args.recipe)
    recipe.run()