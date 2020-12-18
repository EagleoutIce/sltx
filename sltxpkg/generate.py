import sltxpkg.prompt as prompt
import os

import yaml
from yaml.representer import SafeRepresenter

import sltxpkg.globals as sg
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


def assure_workflow_target(path: str):
	if os.path.isfile(path):
		print("A workflow-file with the given name does already exist!")
		overwrite = prompt.get_bool(default=False)
		if not overwrite:
			print("Aborting...")
			exit(1)
	basepath = os.path.dirname(path)
	if basepath is None or basepath.strip() == "":
		return

	if not os.path.isdir(basepath):
		print("The directory", basepath, "does not exist. should it be created?")
		create = prompt.get_bool(default=True)
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
	lfs = prompt.get_bool("Checkout lfs ", default=True)
	submodules = prompt.get_bool("Checkout submodules ", default=True)
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


def step_setup_sltx(document: dict) -> str:
	# tODO get them with 'docker search' # TODO dry
	valid_profiles = ['tx-small', 'tx-default', 'tx-full']
	print("Please enter the profile you want for sltx. Valid names are:", valid_profiles)
	target_profile = prompt.get(
		"Profile [{default}]", default=sg.configuration[sg.C_DOCKER_PROFILE]).lower()

	# TODO: we need a option for additional dependencies
	setup_lines = "echo \"" + target_profile + "\" | sltx docker"

	add_step(document,
			 "Setup and run sltx-install",
			 _run=YamlBlock("pip install sltx\n" +
							setup_lines + "\n")
			 )
	return target_profile


def step_compile(document: dict, target_profile: str):
	print("Do you need your own config file to compile?")
	own_config = prompt.get_bool(default=False)
	config_file = None
	if own_config:
		config_file = prompt.get_file("Path to config-file")

	print("Which documents do you want to have compiled? You may separate multiple ones by comma.")
	file_list = prompt.get("File(s)")
	files = file_list.split(',')

	exec_line = "sltx "

	# TODO: fail as soon as one fails
	if own_config and config_file is not None:
		exec_line += "--config \"{config_file}\" ".format(**locals())

	# TODO: recipe support!
	# NOTE: root is required for now due to permission errors in action container
	# this is only for gha
	exec_line += "compile --root --profile \"" + target_profile + "\" "  + " ".join(['"' + f + '"' for f in files]) + "\n"

	add_step(document,
			 "Compile the Documents",
			 _run=YamlBlock(exec_line)
			 )
	return files


def step_commit_and_push(document: dict, files: list):
	print("Do you want the resulting pdf(s) to be pushed?")
	do_push = prompt.get_bool(default=True)

	if not do_push:
		return

	files = [os.path.splitext(f)[0] + ".pdf" for f in files]

	print("Which documents do you want to have pushed? You may separate multiple ones by comma.")
	print("Default:", files)
	push_file_list = prompt.get("Doc(s)", default="")
	if push_file_list.strip() != "":
		files = push_file_list.split(',')

	add_line = "git add -f " + \
		" ".join(["\"" + f + "\"" for f in files]) + "\n"

	# commit
	add_step(document,
			 "Commit",
			 _run=YamlBlock(
				 "git config --local user.email \"action@github.com\"\ngit config --local user.name \"GitHub Action\"\n" +
				 add_line + "git commit -m \"Newly compiled data\"\n"))

	# push
	branch = prompt.get("Push-Branch [{default}]", default="gh-pages")
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
	target_path = prompt.get(
		"Workflow-Path [{default}]", default=".github/workflows/compile.yaml")
	assure_workflow_target(target_path)

	document['name'] = prompt.get("Workflow name")
	document['on'] = {'push': {'branches': ['master','main']}}
	document['jobs'] = {
		'build': {
			'runs-on': 'ubuntu-latest',
			'steps': []
		}
	}

	step_checkout(document)
	step_setup_python(document)
	profile = step_setup_sltx(document)
	files = step_compile(document, profile)
	step_commit_and_push(document, files)

	print("Ok, I will write the file now...")
	with open(target_path, 'tw') as f:
		# We will disable this to get name on top and have no sorting
		stream = yaml.dump(document, default_flow_style=False, sort_keys=False)
		# formatting a little bit?
		f.write(stream.replace('jobs:', '\njobs:'))
	print("File written to \"" + target_path + "\". Job completed.")
