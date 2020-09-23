# Docker control
from sltxpkg.globals import DOCKER_URL
import docker
import json

# TODO for now we need a reading PAT? 

class DockerCtrl:
    def __init__(self):
        self.client = docker.from_env()
        self.client.ping()

    def update_img(self, profile : str):
        target = DOCKER_URL.format(**locals())
        print("Pulling image:", target, "this may take a few minutes")
        for line in self.client.api.pull(target, tag='latest',stream=True):
            # default values
            d = {'status': 'unknown', 'progress':'', 'id':''}
            d = {**d, **json.loads(line)}
            print("   {status} {progress} {id}".format(**d))
