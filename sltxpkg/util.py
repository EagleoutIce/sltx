from sys import platform


def default_texmf():
    if platform == "linux" or platform == "linux2":
        return "~/texmf"
    elif platform == "darwin":
        return "~/Library/texmf"
    elif platform == "win32":
        return "~/texmf"


def get_version():
    with open('version.info', 'r') as vi:
        return vi.readline()
