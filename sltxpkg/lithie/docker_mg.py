# Docker control
import json
import os

import docker
from sltxpkg.globals import DOCKER_URL

# TODO for now we need a reading PAT?


class DockerCtrl:
    def __init__(self):
        self.client = docker.from_env()
        self.client.ping()

    def update_img(self, profile: str):
        target = DOCKER_URL.format(**locals())
        print("Pulling image:", target, "this may take a few minutes")
        for line in self.client.api.pull(target, tag='latest', stream=True):
            # default values
            d = {'status': 'unknown', 'progress': '', 'id': ''}
            d = {**d, **json.loads(line)}
            print("   {status} {progress} {id}".format(**d))

    def run_in_container(self, profile: str, command: str):
        target = DOCKER_URL.format(**locals())
        run = self.client.containers.run(
            target, command=command, detach=True, remove=True, working_dir='/home',
            volumes={
                os.getcwd(): {
                    'bind': '/home',
                    'mount': 'rw'
                }
            })
        for l in run.logs(stdout=True, stderr=True, stream=True, timestamps=True):
            print(l.decode('utf-8'), end='')
