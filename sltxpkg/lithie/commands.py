import sltxpkg.prompt as prompt
from sltxpkg.lithie.docker_mg import DockerCtrl
import sltxpkg.globals as sg
import sltxpkg.config as sc

# TODO: get valid names
def install():
	valid_profiles=['tx-small', 'tx-default', 'tx-full']
	print("Please enter the profile you want. Valid names are:", valid_profiles)
	target = prompt.get("Profile [{default}]", default=sg.configuration[sg.C_DOCKER_PROFILE]).lower()
	# TODO: do not exit, try anyway
	if target not in valid_profiles:
		print(target, "was not found in", valid_profiles, "exiting for now")
		exit(1)

	_install(target)

def _install(target: str):
	docker_ctrl = DockerCtrl()
	docker_ctrl.update_img(target)

# TODO: clarify time in docker container as it is utc it must be the same as host!!!!
# TODO: keep container running to avoid full recompilations each time? (this should be the optimum!!)
# TODO: optimal would be to mount the working dir to the real world outside working dir to have it detached but saved
# TODO: in this case cleaning would not be needed!
def compile():
	sc.assure_dirs()
	docker_ctrl = DockerCtrl()
	profile = sg.configuration[sg.C_DOCKER_PROFILE] if sg.args.profile is None else sg.args.profile
	sltx_command = "sltx -t " + str(sg.args.threads) + " "

	if sg.args.quiet:
		sltx_command += "--quiet "

	if sg.args.config is not None:
		sltx_command += "--config \"" + sg.args.config + "\" "

	sltx_command += "raw-compile "

	if sg.args.recipe is not None:
		sltx_command += "--recipe \"" + sg.args.recipe + "\" "

	if sg.args.extra_arguments is not None:
		sltx_command += "--args=\"" + " ".join(sg.args.extra_arguments) + "\" "

	for dep in sg.args.extra_dependencies:
		# will extend the dict with 'new' ones
		# should work even better if sltx-source.yaml files are present in the targets
		sltx_command += "--dependency \"" + dep + "\" "

	sltx_command += " ".join(['"' + f + '"' for f in sg.args.files])

	print("Running command in docker: " + sltx_command)
	docker_ctrl.run_in_container(sg.args.dock_as_root, profile, sltx_command)