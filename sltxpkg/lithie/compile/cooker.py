# cookes the recipe :D
from concurrent import futures
import sys

import sltxpkg.globals as sg
from sltxpkg.lithie.compile.recipe import Recipe
import sltxpkg.lithie.compile.recipe_exceptions as rex


def cook():
    recipe_path = sg.configuration[sg.C_DEFAULT_RECIPE] if sg.args.recipe is None else sg.args.recipe

    with futures.ThreadPoolExecutor(max_workers=sg.args.threads) as pool:
        runners = []
        for i, file in enumerate(sg.args.files):
            recipe = Recipe(recipe_path, file, i)
            runners.append((pool.submit(recipe.run), i, file))
        futures.wait([r[0] for r in runners])
        try:
            for runner, i, file in runners:
                if runner.result() is not None:
                    sg.LOGGER.info(
                        "Status for runner: %d operating on file: %s", i, file)
                    sg.LOGGER.info(runner.result())
        except rex.RecipeException as ex:
            print("\n\033[31m ! Processing of", file,
                  "failed for:", repr(ex), "\033[m")
            sys.exit(128)
        else:
            sg.LOGGER.info("\n=Compiled all documents successfully=")
