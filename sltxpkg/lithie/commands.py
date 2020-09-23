import sltxpkg.prompt as prompt
from sltxpkg.lithie.docker_mg import DockerCtrl
import sltxpkg.globals as sg

# TODO: get valid names
def install():
    valid_profiles=['tx-small', 'tx-default', 'tx-full']
    print("Please enter the profile you want. Valid names are:", valid_profiles)
    target = prompt.get("Profile [{default}]", default=sg.configuration[sg.C_DOCKER_PROFILE]).lower()
    # TODO: do not exit, try anyway
    if target not in valid_profiles:
        print(target, "was not found in", valid_profiles, "exiting for now")
        exit(1)
    docker_ctrl = DockerCtrl()
    docker_ctrl.update_img(target)

def compile():
    docker_ctrl = DockerCtrl()
    profile = sg.configuration[sg.C_DOCKER_PROFILE] if sg.args.profile is None else sg.args.profile
    docker_ctrl.run_in_container(profile, "touch 123.txt")