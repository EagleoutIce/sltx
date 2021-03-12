class RecipeException(Exception):

    def __init__(self, filename, message):
        self.filename = filename
        self.message = message
        super().__init__(self.message)
