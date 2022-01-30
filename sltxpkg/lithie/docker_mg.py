# Docker control
import json
import os
import sys

import docker

import sltxpkg.globals as sg
import sltxpkg.util as su
from sltxpkg.globals import DOCKER_URL
from sltxpkg.log_control import LOGGER


class DockerCtrl:
    def __init__(self):
        self.client = docker.from_env()
        self.client.ping()

    def update_img(self, profile: str):
        target = DOCKER_URL.format(**locals())
        LOGGER.info("Pulling image: %s this may take a few minutes", target)
        for line in self.client.api.pull(target, tag='latest', stream=True):
            # default values
            line = line.decode('utf-8')
            lines = line.split('\r\n')
            for subline in lines:
                if subline is None or subline.strip() == "":
                    continue
                d = {'status': 'unknown', 'progress': '', 'id': ''}
                d = {**d, **json.loads(subline)}
                LOGGER.info("   {status} {progress} {id}".format(**d))

    # tODO: autocache name with unique path needs to use real file name not docker!!

    def run_in_container(self, root: bool, profile: str, command: str):
        if profile.startswith(":"):
            target = profile[1:]
        else:
            target = DOCKER_URL.format(**locals())
        LOGGER.info("Launching container based on image: " + target)
        if root:
            LOGGER.warning(
                "Using root configuration. This might lead to permission errors in the future. " + target)
        # TODO: this must be expanded better and safer, this way only '~' might be used which is bad
        wd = sg.configuration[sg.C_WORKING_DIR].replace(
            os.path.expanduser('~'), '/root')
        LOGGER.info("  - Note: Working-Dir bound to: %s for %s",
                    wd, sg.configuration[sg.C_WORKING_DIR])
        LOGGER.info(
            "  - Note: Main-Dir bound to: /root/data for " + os.getcwd())
        volumes = {
            os.getcwd(): {
                'bind': '/root/data',
                'mount': 'rw'
            },
            sg.configuration[sg.C_WORKING_DIR]: {
                'bind': wd,
                'mount': 'rw'
            }
        }
        if sg.args.local_texmf:
            target_mount = "/usr/share/sltx/texmf"
            LOGGER.info("  - Note: Mounting local txmf-tree (%s) to %s",
                        su.get_tex_home(), target_mount)
            volumes[su.get_tex_home()] = {
                'bind': target_mount,
                'mount': 'rw'
            }
        run = self.client.containers.run(
            target, command = command, detach = True, remove = False, working_dir = '/root/data', tty = True,
            network_mode = 'bridge', user = 'root' if root else 'lithie-user',
            volumes = volumes)
        # We need a buffer in case a multibyte unicode sequence
        # will be broken at line end
        buffer=b''
        for l in run.logs(stdout = True, stderr = True, stream = True, timestamps = True):
            try:
                LOGGER.info('\u0001' + (buffer + l).decode('utf-8'))
                buffer=b''
            except UnicodeDecodeError as ex:
                buffer += l
        LOGGER.info("Container completed.")
        feedback=run.wait()
        run.remove()
        if 'StatusCode' in feedback and feedback['StatusCode'] != 0:
            code=feedback['StatusCode']
            LOGGER.error("Command failed with: " + str(code))
            sys.exit(code)
