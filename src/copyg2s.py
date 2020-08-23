import json
import locale
import os

import config
import gphotos
import gsheets
import serverintf


# copy Google sheets to (Location)Server
class CopyG2S:
    def __init__(self, base):
        self.baseConfig = config.Config()
        self.selected_base = base
        self.baseJS = self.baseConfig.getBase(self.selected_base)
        self.serverIntf = serverintf.ServerIntf(self.baseJS)
        try:
            self.message("Mit Google Sheets verbinden")
            self.gsheet = gsheets.GSheet(self)
        except Exception as e:
            self.message("Kann Google Sheets nicht erreichen:" + str(e))
            raise (e)

        try:
            userInfo = self.gsheet.get_user_info(self.gsheet.getCreds())
            self.message("Mit Google Photos verbinden als " + userInfo["name"])
            self.gphoto = gphotos.GPhoto(self)
        except Exception as e:
            self.message("Kann Google Photos nicht erreichen:" + str(e))
            raise (e)

    def copyg2s(self):
        minlat = -90.0
        maxlat = 90.0
        minlon = 0.0
        maxlon = 180.0
        if not os.path.exists("gsheets.json"):
            sheetValues = self.gsheet.getValuesWithin(-90.0, 90.0, -180.0, 180.0)
            with open("gsheets.json", "w") as jsonFile:
                json.dump(sheetValues, jsonFile, indent=4)
        else:
            with open("gsheets.json", "r") as jsonFile:
                sheetValues = json.load(jsonFile)

        dbValues = serverintf.convertG2S(sheetValues)
        for tablename in dbValues.keys():
            vals = dbValues[tablename]
            print("post", tablename)
            if tablename.endswith("_images"):
                for val in vals:
                    self.serverIntf.imgpost(tablename, val)
            else:
                self.serverIntf.post(tablename, vals)

    """
    daten:    ['OSM', 'OSM', 'OSM', '48,1412437', '11,5594636', '48,14124', '11,55946']
    images: ['Muh', '2020.05.25 16:26:13', '48,0859442', '11,5359655', '48,08594', '11,53597',
     'ACKY64tZN25Z4Pn4ixE6JoKK-LYlKrsLmI9VPVuWldVos6CNd_0I7xBimLiwYyn_6RIlYQYRmoJ7KqlueUfywnGePrDee8RqiA',
     'https://photos.google.com/lr/album/ACKY64u2oPLRfQInuxAI_WCx_bF2C589MQPuVc2jxBcaCI9zm2Oqrl9Nq3kba8Nz_s_iyDMvtZR8/photo/ACKY64tZN25Z4Pn4ixE6JoKK-LYlKrsLmI9VPVuWldVos6CNd_0I7xBimLiwYyn_6RIlYQYRmoJ7KqlueUfywnGePrDee8RqiA']
    zusatz: ['1', 'MUH', '2020.05.19 10:54:03', '2020.05.19 10:54:16', '48,1425199', '11,5903107', '48,14252', '11,59031',
     'gut', '30', 'Soso']
    """

    def message(self, *args):
        print(*args)


if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = CopyG2S("Abstellanlagen")
    app.copyg2s()
