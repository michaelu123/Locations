import glob
import json

import utils


class Config():
    def __init__(self, app):
        self.app = app
        configDir = utils.getDataDir()
        self.configs = {}
        for dir in set([configDir, "."]):
            self.file_list = sorted(glob.glob(dir + "/config/*.json"))
            for f in self.file_list:
                try:
                    with open(f, "r", encoding="UTF-8") as jsonFile:
                        confJS = json.load(jsonFile)
                        if confJS.get("name") is None:
                            continue
                        nm = confJS.get("name")
                        self.configs[nm] = confJS
                        print("gelesen:", f, nm)
                except Exception as e:
                    utils.printEx("Fehler beim Lesen von " + f, e)

    def getGPSArea(self, name):
        gps = self.configs[name].get("gps")
        # (11.4, 48.0, 11.8, 48.25) = München
        return (gps.get("min_lon"), gps.get("min_lat"), gps.get("max_lon"), gps.get("max_lat"))

    def getNames(self):
        return list(self.configs.keys())

    def getMinZoom(self, name):
        gps = self.configs[name].get("gps")
        return gps.get("min_zoom")

    def getBase(self, name):
        return self.configs[name]
