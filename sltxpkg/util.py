from sys import platform


def default_texmf():
    if platform == "linux" or platform == "linux2":
        return "~/texmf"
    elif platform == "darwin":
        return "~/Library/texmf"
    elif platform == "win32":
        return "~/texmf"
