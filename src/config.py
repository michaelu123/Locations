import glob
import json

import utils

class Config():
    def __init__(self):
        configDir = utils.getDataDir()
        self.file_list = sorted(glob.glob(configDir + "/config/*.json"))
        self.configs = {}
        for f in self.file_list:
            try:
                with open(f, "r",encoding="UTF-8") as jsonFile:
                    confJS = json.load(jsonFile)
                    if confJS.get("name") is None:
                        continue
                    self.configs[confJS.get("name")] = confJS
            except Exception as e:
                s = utils.printExToString("Fehler beim Lesen der Datei " + f, e)
                print(s)
                try:
                    popup = utils.MsgPopup(s)
                    popup.open()
                except:
                    pass
        pass

    def getGPSArea(self, name):
        gps = self.configs[name].get("gps")
        return (gps.get("min_lon"), gps.get("min_lat"), gps.get("max_lon"), gps.get("max_lat"))  # (11.4, 48.0, 11.8, 48.25) = München

    def getNames(self):
        return self.configs.keys()

    def getMinZoom(self, name):
        gps = self.configs[name].get("gps")
        return gps.get("min_zoom")

    def getBase(self, name):
        return self.configs[name]

if __name__ == '__main__':
    x = Config()


