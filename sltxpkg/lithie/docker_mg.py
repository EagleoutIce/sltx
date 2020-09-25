# Docker control
import json
import os

import docker
from sltxpkg.globals import DOCKER_URL


class DockerCtrl:
    def __init__(self):
        self.client = docker.from_env()
        self.client.ping()

    def update_img(self, profile: str):
        target = DOCKER_URL.format(**locals())
        print("Pulling image:", target, "this may take a few minutes")
        for line in self.client.api.pull(target, tag='latest', stream=True):
            # default values
            line = line.decode('utf-8')
            lines = line.split('\r\n')
            for subline in lines:
                if subline is None or subline.strip() == "":
                    continue
                d = {'status': 'unknown', 'progress': '', 'id': ''}
                d = {**d, **json.loads(subline)}
                print("   {status} {progress} {id}".format(**d))

    def run_in_container(self, profile: str, command: str):
        if profile.startswith(":"):
            target = profile[1:]
        else:
            target = DOCKER_URL.format(**locals())
        print("Launching container", target)
        run = self.client.containers.run(
            target, command=command, detach=True, remove=True, working_dir='/root/data',
            user='root', privileged=True, network_mode='bridge',
            volumes={
                os.getcwd(): {
                    'bind': '/root/data',
                    'mount': 'rw'
                }
            })
        for l in run.logs(stdout=True, stderr=True, stream=True, timestamps=True):
            print(l.decode('utf-8'), end='')
        print("Container completed.")
