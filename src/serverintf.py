import http.client as htcl
import json
import os
from datetime import datetime

import utils

# MSSQL types
sqtype = {"int": "INT", "bool": "TINYINT", "prozent": "TINYINT", "string": "VARCHAR(2048)", "float": "DOUBLE"}

# LOCATIONSSERVER = "raspberrylan.1qgrvqjevtodmryr.myfritz.net"
# LOCATIONSSERVER_PORT = 80
# LOCATIONSSERVER = "localhost"
# LOCATIONSSERVER_PORT=5000

class ServerIntf:
    def __init__(self, app):
        self.baseJS = app.baseJS
        self.dbinst = app.dbinst
        self.url = app.getConfigValue("serverName", "localhost")
        self.port = int(app.getConfigValue("serverPort", 80))
        self.lsconn = htcl.HTTPConnection(self.url, port=self.port)
        self.tabellenname = self.baseJS.get("db_tabellenname")
        self.sayHello()

    def reqWithRetry(self, *args, **kwargs):
        try:
            self.lsconn.request(*args, **kwargs)
            resp = self.lsconn.getresponse()
        except:
            self.lsconn.close()
            self.lsconn = htcl.HTTPConnection(self.url, self.port)
            self.lsconn.request(*args, **kwargs)
            resp = self.lsconn.getresponse()
        return resp

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
                    if val["image_url"].startswith("http"):
                        filename = self.gphoto.getImage(val["image_path"])
                        val["image_url"] = filename  # './images/4032x3024_48.08594_11.53597_20200525_162515.jpg'
            dbValues[tablename] = vals
        return dbValues

    def sayHello(self):
        req = "/tables"
        resp = self.reqWithRetry("GET", req)
        if resp.status != 200:
            raise ValueError("Keine Verbindung zum LocationsServer")
        js = json.loads(resp.read().decode("utf-8"))
        # js = ['abstellanlagen_daten', 'abstellanlagen_images', 'abstellanlagen_zusatz']
        for j in js:
            if j == self.tabellenname + "_daten":
                return
        raise ValueError("Keine Tabelle " + self.tabellenname + "_daten auf dem LocationsServer gefunden")

    # get the image from Google and store it on the server,
    # and insert a row into the LocationsServer DB
    def imgpost(self, tablename, val):
        url = val["image_url"]
        x = url.find("_")
        basename = url[x + 1:]
        headers = {"Content-type": "image/jpeg"}
        req = f"/addimage/{tablename}/{basename}"
        with open(url, "rb") as img:
            body = img.read()
        resp = self.reqWithRetry("POST", req, body, headers)
        print(basename, resp.status, resp.reason)
        if resp.status != 200:
            raise ValueError("Konnte Photo nicht hochladen")
        js = json.loads(resp.read().decode("utf-8"))
        val["image_url"] = js["url"]
        self.post(tablename, val)

    def post(self, tablename, vals):
        req = "/add/" + tablename
        headers = {"Content-type": "application/json"}
        js = json.dumps(vals)
        resp = self.reqWithRetry("POST", req, js, headers)
        sta = resp.status
        if sta != 200:
            print("Error", tablename, sta, resp.reason, vals)
        else:
            js = json.loads(resp.read().decode("utf-8"))
            print("Result", js)

    def getValuesWithin(self, minlat, maxlat, minlon, maxlon):
        tablenames = [self.tabellenname + "_daten", self.tabellenname + "_images", self.tabellenname + "_zusatz"]
        res = {}
        for tname in tablenames:
            req = f"/region/{tname}?minlat={minlat}&maxlat={maxlat}&minlon={minlon}&maxlon={maxlon}"
            resp = self.reqWithRetry("GET", req)
            if resp.status != 200:
                raise ValueError("Keine Verbindung zum LocationsServer")
            js = json.loads(resp.read().decode("utf-8"))
            res[tname] = js
        return res

    def getImage(self, basename, maxdim):
        print("getImage", basename, maxdim)  # getImage 48.08127_11.52709_20200525_165425.jpg 200 200
        filename = utils.getDataDir() + f"/images/{maxdim}_{basename}"
        if os.path.exists(filename):
            return filename

        tablename = self.tabellenname + "_images"
        req = f"/getimage/{tablename}/{basename}?maxdim={maxdim}"
        resp = self.reqWithRetry("GET", req)
        if resp.status != 200:
            print("getImage resp", resp.status, resp.reason)
            return None
        img = resp.read()
        with open(filename, "wb") as f:
            f.write(img)
        return filename

    def upload_photos(self, photos):
        tablename = self.tabellenname + "_images"
        headers = {"Content-type": "image/jpeg"}
        for photo in photos:
            print("upload", photo)
            filepath = photo["filepath"]
            basename = os.path.basename(filepath)
            req = f"/addimage/{tablename}/{basename}"
            with open(filepath, "rb") as img:
                body = img.read()
            resp = self.reqWithRetry("POST", req, body, headers)
            print(basename, resp.status, resp.reason)
            if resp.status != 200:
                raise ValueError("Konnte Photo nicht hochladen")
            js = json.loads(resp.read().decode("utf-8"))
            photo["id"] = basename
            photo["url"] = js["url"]
            pass

    def appendValues(self, table_name, vals):
        print("appendValues", table_name, vals)
        colnames = self.dbinst.colNamesFor(table_name)
        newvals = []
        for val in vals:
            newvals.append(dict(zip(colnames, val)))
        self.post(table_name, newvals)
