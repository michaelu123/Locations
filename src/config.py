import glob
import json

import utils


class Config():
    def __init__(self, app):
        self.app = app
        configDir = utils.getDataDir()
        self.file_list = sorted(glob.glob(configDir + "/config/*.json"))
        self.configs = {}
        for f in self.file_list:
            with open(f, "r", encoding="UTF-8") as jsonFile:
                confJS = json.load(jsonFile)
                if confJS.get("name") is None:
                    continue
                self.configs[confJS.get("name")] = confJS

    def getGPSArea(self, name):
        gps = self.configs[name].get("gps")
        # (11.4, 48.0, 11.8, 48.25) = München
        return (gps.get("min_lon"), gps.get("min_lat"), gps.get("max_lon"), gps.get("max_lat"))

    def getNames(self):
        return self.configs.keys()

    def getMinZoom(self, name):
        gps = self.configs[name].get("gps")
        return gps.get("min_zoom")

    def getBase(self, name):
        return self.configs[name]
