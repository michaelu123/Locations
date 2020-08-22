import json
import locale
from datetime import datetime

import config
import gphotos
import gsheets

# MSSQL types
sqtype = {"int": "INT", "bool": "TINYINT", "prozent": "TINYINT", "string": "VARCHAR(2048)", "float": "DOUBLE"}

# copy Google sheets to LocationServer
class CopyG2S:
    def __init__(self, base):
        self.baseConfig = config.Config()
        self.selected_base = base
        self.baseJS = self.baseConfig.getBase(self.selected_base)
        try:
            self.message("Mit Google Sheets verbinden")
            self.gsheet = gsheets.GSheet(self)
        except Exception as e:
            self.message("Kann Google Sheets nicht erreichen:" + str(e))
            raise(e)

        try:
            userInfo = self.gsheet.get_user_info(self.gsheet.getCreds())
            self.message("Mit Google Photos verbinden als " + userInfo["name"])
            self.gphoto = gphotos.GPhoto(self)
        except Exception as e:
            self.message("Kann Google Photos nicht erreichen:" + str(e))
            raise(e)

    def copyg2s(self):
        minlat = -90.0
        maxlat = 90.0
        minlon = 0.0
        maxlon = 180.0
        # sheetValues = self.gsheet.getValuesWithin(-90.0, 90.0, -180.0, 180.0)
        # with open("gsheets.json", "w") as jsonFile:
        #     json.dump(sheetValues, jsonFile, indent=4)
        with open("gsheets.json", "r") as jsonFile:
            sheetValues = json.load(jsonFile)
        for tablename in sheetValues.keys():
            if tablename.endswith("_daten"):
                colnames = ["creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
                floatcols = [3, 4, 5, 6]
                for i, feld in enumerate(self.baseJS.get("daten").get("felder")):
                    name = feld.get("name")
                    colnames.append(name)
                    type = sqtype[feld.get("type")]
                    if type == "DOUBLE":
                        floatcols.append(i + 7)
            elif tablename.endswith("_images"):
                colnames = ["creator", "created", "lat", "lon", "lat_round", "lon_round", "image_path", "image_url"]
                floatcols = [2, 3, 4, 5]
            elif tablename.endswith("_zusatz"):
                colnames = ["nr", "creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
                floatcols = [4, 5, 6, 7]
                for i, feld in enumerate(self.baseJS.get("zusatz").get("felder")):
                    name = feld.get("name")
                    colnames.append(name)
                    type = sqtype[feld.get("type")]
                    if type == "DOUBLE":
                        floatcols.append(i + 8)

            vals = []
            for row in sheetValues[tablename]:
                val = {}
                for i in floatcols:
                    row[i] = float(row[i].replace(",", "."))
                for i, cname in enumerate(colnames):
                    if cname == "created":
                        val[cname] = self.toIso(row[i])
                    elif cname.endswith("_round"):
                        val[cname] = str(row[i])
                    else:
                        if i < len(row):
                            v = row[i]
                            if v == "":
                                v = None
                        else:
                            v = None
                        val[cname] = v
                vals.append(val)
                # build chunks?

            if tablename.endswith("_images"):
                for val in vals:
                    if val["image_url"].startswith("https"):
                        filename = self.gphoto.getImage(val["image_path"])
                        val["image_url"] = filename  # './images/4032x3024_48.08594_11.53597_20200525_162515.jpg'
                        self.imgpost(tablename, val)
            else:
                self.post(tablename, vals)

    def imgpost(self, tablename, val):
        pass

    def post(self, tablename, vals):
        pass

    def toIso(self, d):
        # d= 'ISO' or '2020.05.25 16:26:13'
        if len(d) != 19:
            return d
        yr = int(d[0:4])
        mo = int(d[5:7])
        dy = int(d[8:10])
        hh = int(d[11:13])
        mm = int(d[14:16])
        ss = int(d[17:19])
        dt = datetime(yr, mo, dy, hour=hh, minute=mm, second=ss)
        return dt.isoformat()

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
    # nc = True
    # x = MyMapMarker(lat=0, lon=0, nocache=nc)
    # print("size1", utils.getsize(x))
    # y = []
    # for i in range(100):
    #     y.append(MyMapMarker(lat=0, lon=0, nocache=nc))
    # print("size100", utils.getsize(y))
    # Cache.print_usage()

    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = CopyG2S("Abstellanlagen")
    app.copyg2s()

