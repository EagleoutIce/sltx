import os

import yaml
from yaml.representer import SafeRepresenter

from sltxpkg.globals import C_TEX_HOME

# https://stackoverflow.com/a/20863889


def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer


class YamlBlock(str):
    pass


represent_literal_str = change_style('|', SafeRepresenter.represent_str)
yaml.add_representer(YamlBlock, represent_literal_str)


def valid_default(inp: str):
    return inp is not None and inp.strip() != ""


def valid_dir(inp: str):
    return valid_default(inp) and os.path.isdir(inp)


def valid_file(inp: str):
    return valid_default(inp) and os.path.isfile(inp)


def get_from_user(prompt: str, valid_input=valid_default, type=str, default=None):
    got = None
    prompt = "\033[36m" + prompt.format(**locals()) + ">\033[m "
    if default is None:
        while not valid_input(got):
            got = input(prompt)
    else:
        got = input(prompt)
    ret = type(default if not valid_input(got) else got)
    return ret


def get_bool(pre="", default=None):
    if default is None:
        prompt = "[true/false]"
    elif default:
        prompt = "[TRUE/false]"
    else:
        prompt = "[True/FALSE]"

    return get_from_user(pre + prompt, type=bool, default=default)


def get_dir(prompt: str, default=None):
    return get_from_user(prompt, valid_input=valid_dir, type=str, default=default)


def get_file(prompt: str, default=None):
    return get_from_user(prompt, valid_input=valid_file, type=str, default=default)


def assure_workflow_target(path: str):
    if os.path.isfile(path):
        print("A workflow-file with the given name does already exist!")
        overwrite = get_bool(default=False)
        if not overwrite:
            print("Aborting...")
            exit(1)
    basepath = os.path.dirname(path)
    if basepath is None or basepath.strip() == "":
        return

    if not os.path.isdir(basepath):
        print("The directory", basepath, "does not exist. should it be created?")
        create = get_bool(default=True)
        if not create:
            print("Aborting...")
            exit(1)
        os.makedirs(basepath)


def add_step(document: dict, name: str, uses: str = None, _with: dict = None, _run: str = None):
    step = {'name': name}
    if uses is not None:
        step['uses'] = uses
    if _with is not None:
        step['with'] = _with
    if _run is not None:
        step['run'] = _run
    document['jobs']['build']['steps'].append(step)


def step_checkout(document: dict):
    lfs = get_bool("Checkout lfs ", default=True)
    submodules = get_bool("Checkout submodules ", default=True)
    add_step(document,
             "Checkout git repository",
             uses="actions/checkout@v2",
             _with={
                 'lfs': lfs,
                 'submodules': submodules
             })


def step_setup_python(document: dict):
    add_step(document,
             "Setup Python environment for sltx",
             uses="actions/setup-python@v2",
             _with={
                 'python-version': '3.8'
             })


def step_setup_sltx(document: dict):
    print("Do you need your own config file for sltx?")
    own_config = get_bool(default=False)
    config_file = ".sltx-gh-conf.yaml"
    texmf_home = "./texmf/tex/latex/sltx"
    dep_file = "sltx-dep.yml"
    setup_lines = ""

    if own_config:
        config_file = get_file("Path to config-file")
        print("Make sure you have set {C_TEX_HOME} to {texmf_home}".format(
            **globals(), **locals()))
    else:
        setup_lines += "echo \"{C_TEX_HOME}: {texmf_home}\" > \"{config_file}\"\n".format(
            **globals(), **locals())

    dep_file = get_file("Path to dep-file [{default}]", default=dep_file)

    exec_line = "sltx --config \"{config_file}\" --dependencies \"{dep_file}\"".format(
        **locals())

    add_step(document,
             "Setup and run sltx-install",
             _run=YamlBlock("pip install sltx\n" +
                            setup_lines + exec_line + "\n")
             )


def step_compile(document: dict):
    print("Which documents do you want to have compiled? You may separate multiple ones by comma.")
    file_list = get_from_user("File(s)")
    files = file_list.split(',')

    exec_lines = "tlmgr conf texmf TEXMFHOME \"~/Library/texmf:./texmf\"\n"

    args = "-pdf -file-line-error -halt-on-error -interaction=nonstopmode"

    for file in files:
        exec_lines += "latexmk " + args + " \"" + file + "\" && "
    exec_lines += "\n"
    add_step(document,
             "Setup Texlive and compile the documents",
             uses="xu-cheng/texlive-action/full@v1",
             _with={
                 'run': YamlBlock(exec_lines)
             })
    return files


def step_commit_and_push(document: dict, files: list):
    print("Do you want the resulting pdf(s) to be pushed?")
    do_push = get_bool(default=True)

    if not do_push:
        return

    files = [os.path.splitext(f)[0] + ".pdf" for f in files]

    print("Which documents do you want to have pushed? You may separate multiple ones by comma.")
    print("Default:", files)
    push_file_list = get_from_user("Doc(s)", default="")
    if push_file_list.strip() != "":
        files = push_file_list.split(',')

    add_line = "git add -f " + " ".join(["\"" + f + "\"" for f in files]) + "\n"

    # commit
    add_step(document,
             "Commit",
             _run=YamlBlock(
                 "git config --local user.email \"action@github.com\"\ngit config --local user.name \"GitHub Action\"\n" + 
                 add_line + "git commit -m \"Newly compiled data\"\n"))

    # push
    branch = get_from_user("Push-Branch [{default}]", default="gh-pages")
    add_step(document,
             "Push changes",
             uses="ad-m/github-push-action@master",
             _with={
                    'branch': branch,
                    'github_token': "${{ secrets.GITHUB_TOKEN }}",
                    'force': True
             })


def generate():
    document = {}

    print("We will now generate a GitHub-Action workflow")
    target_path = get_from_user(
        "Workflow-Path [{default}]", default=".github/workflows/compile.yaml")
    assure_workflow_target(target_path)

    document['name'] = get_from_user("Workflow name")
    document['on'] = {'push': {'branches': ['master']}}
    document['jobs'] = {
        'build': {
            'runs-on': 'ubuntu-latest',
            'steps': []
        }
    }

    step_checkout(document)
    step_setup_python(document)
    step_setup_sltx(document)
    files = step_compile(document)
    step_commit_and_push(document, files)

    print("Ok, I will write the file now...")
    with open(target_path, 'tw') as f:
        # We will disable this to get name on top and have no sorting
        stream = yaml.dump(document, default_flow_style=False, sort_keys=False)
        # formatting a little bit?
        f.write(stream.replace('jobs:', '\njobs:'))
    print("File written to \"" + target_path + "\". Job completed.")
