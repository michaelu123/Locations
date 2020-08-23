import http.client as htcl
import json
from datetime import datetime

# MSSQL types
sqtype = {"int": "INT", "bool": "TINYINT", "prozent": "TINYINT", "string": "VARCHAR(2048)", "float": "DOUBLE"}


class ServerIntf:
    def __init__(self, baseJS):
        self.baseJS = baseJS
        self.lsconn = htcl.HTTPConnection("localhost", port=5000)
        self.tabellenname = self.baseJS.get("db_tabellenname")
        self.sayHello()

    def toIso(self, d):
        # d= 'ISO' or '2020.05.25 16:26:13'
        if len(d) != 19:
            d = "2000.01.01 01:00:00"
        yr = int(d[0:4])
        mo = int(d[5:7])
        dy = int(d[8:10])
        hh = int(d[11:13])
        mm = int(d[14:16])
        ss = int(d[17:19])
        dt = datetime(yr, mo, dy, hour=hh, minute=mm, second=ss)
        return dt.isoformat()

    def convertG2S(self, sheetValues):
        dbValues = {}
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
                    if cname == "created" or cname == "modified":
                        val[cname] = self.toIso(row[i])
                    elif cname.endswith("_round"):
                        val[cname] = str(row[i])
                    elif cname == "nr":
                        pass
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

            print("Table", tablename)
            if tablename.endswith("_images"):
                for val in vals:
                    if val["image_url"].startswith("https"):
                        filename = self.gphoto.getImage(val["image_path"])
                        val["image_url"] = filename  # './images/4032x3024_48.08594_11.53597_20200525_162515.jpg'
            dbValues[tablename] = vals
        return dbValues

    def sayHello(self):
        req = "/tables"
        self.lsconn.request("GET", req)
        resp = self.lsconn.getresponse()
        if resp.status != 200:
            raise ValueError("Keine Verbindung zum LocationServer")
        js = json.loads(resp.read().decode("utf-8"))
        # js = ['abstellanlagen_daten', 'abstellanlagen_images', 'abstellanlagen_zusatz']
        for j in js:
            if j == self.tabellenname + "_daten":
                return
        raise ValueError("Keine Tabelle " + tablename + "_daten auf dem LocationServer gefunden")

    # get the image from Google and store it on the server,
    # and insert a row into the LocationServer DB
    def imgpost(self, tablename, val):
        creator = val["creator"]
        created = val["created"]
        lat = str(val["lat"])
        lon = str(val["lon"])
        lat_round = val["lat_round"]
        lon_round = val["lon_round"]
        url = val["image_url"]
        x = url.find("_")
        basename = url[x + 1:]

        req = "/addimage/" + tablename + "?creator=" + creator + "&created=" + created + \
              "&lat=" + lat + "&lon=" + lon + \
              "&lat_round=" + lat_round + "&lon_round=" + lon_round + \
              "&basename=" + basename
        headers = {"Content-type": "image/jpeg"}
        with open(url, "rb") as img:
            body = img.read()
        self.lsconn.request("POST", req, body, headers)
        resp = self.lsconn.getresponse()
        print(basename, resp.status, resp.reason)

    def post(self, tablename, vals):
        req = "/add/" + tablename
        headers = {"Content-type": "application/json"}
        js = json.dumps(vals)
        self.lsconn.request("POST", req, js, headers)
        resp = self.lsconn.getresponse()
        sta = resp.status
        if sta != 200:
            print(tablename, sta, resp.reason, vals)
            return

    def getValuesWithin(self, minlat, maxlat, minlon, maxlon):
        tablenames = [self.tabellenname + "_daten", self.tabellenname + "_images", self.tabellenname + "_zusatz"]
        res = {}
        for tname in tablenames:
            req = f"/region/{tname}?minlat={minlat}&maxlat={maxlat}&minlon={minlon}&maxlon={maxlon}"
            self.lsconn.request("GET", req)
            resp = self.lsconn.getresponse()
            if resp.status != 200:
                raise ValueError("Keine Verbindung zum LocationServer")
            js = json.loads(resp.read().decode("utf-8"))
            res[tname] = js
        return res