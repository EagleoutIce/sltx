# cookes the recipe :D
import sys
from concurrent import futures

import sltxpkg.globals as sg
import sltxpkg.lithie.compile.cooking.recipe_exceptions as rex
from sltxpkg.globals import LOGGER
from sltxpkg.lithie.compile.cooking.recipe import Recipe


def cook():
    """This will take the desired files and cooks the recipes accordingly.
    """
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
                    LOGGER.info(
                        "Status for runner: %d operating on file: %s", i, file)
                    LOGGER.info(runner.result())
        except rex.RecipeException as ex:
            print("\n\033[31m ! Processing of", file,
                  "failed for:", repr(ex), "\033[m")
            sys.exit(128)
        else:
            LOGGER.info("\n=Compiled all documents successfully=")
