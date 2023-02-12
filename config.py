import os
import yaml


class Config:
    cfg = None

    # os.environ['STOCKBALL_HOME'] +
    def __init__(self):
        with open("config.yml", 'r') as file:
            self.cfg = yaml.load(file, Loader=yaml.FullLoader)

    def get(self, key):
        return self.cfg[key]

    def value(self, levels):
        ret = self.cfg[levels[0]]
        for level in levels[1:]:
            ret = ret[level]
        return ret
