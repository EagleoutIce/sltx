import os


def valid_default(inp: str) -> bool:
    return inp is not None and len(inp.strip()) > 0


def valid_dir(inp: str) -> bool:
    return valid_default(inp) and os.path.isdir(inp)


def valid_file(inp: str) -> bool:
    return valid_default(inp) and os.path.isfile(inp)


def get(prompt: str, valid_input=valid_default, type=str, default=None):
    got = None
    prompt = "\033[36m" + prompt.format(**locals()) + ">\033[m "
    if default is None:
        while not valid_input(got):
            got = input(prompt)
    else:
        got = input(prompt)
    ret = type(default if not valid_input(got) else got)
    return ret


def get_bool(pre="", default=None) -> bool:
    if default is None:
        prompt = "[true/false]"
    elif default:
        prompt = "[TRUE/false]"
    else:
        prompt = "[True/FALSE]"

    return get(pre + prompt, type=bool, default=default)


def get_dir(prompt: str, default=None) -> str:
    return get(prompt, valid_input=valid_dir, type=str, default=default)


def get_file(prompt: str, default=None) -> str:
    return get(prompt, valid_input=valid_file, type=str, default=default)
