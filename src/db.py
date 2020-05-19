import sqlite3
import threading
import time

import utils

sqtype = {"int": "INTEGER", "bool": "INTEGER", "prozent": "INTEGER", "string": "TEXT", "float": "REAL"}
threadLocal = threading.local()


class DB():
    _dbinst = None

    @staticmethod
    def instance():
        if DB._dbinst is None:
            DB._dbinst = DB()
        return DB._dbinst

    def getConn(self):
        connMap = getattr(threadLocal, "connMap", None)
        if connMap is None:
            connMap = {}
        dbname = self.baseJS.get("db_name")
        conn = connMap.get(dbname, None)
        if conn is None:
            db = utils.getDataDir() + "/" + dbname
            conn = sqlite3.connect(db)
            connMap[dbname] = conn
        return conn

    def initDB(self, app):
        self.app = app
        self.baseJS = app.baseJS
        self.aliasname = None
        self.tabellenname = self.baseJS.get("db_tabellenname")
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")
        self.colnames = {}
        self.floatcols = {}
        db = utils.getDataDir() + "/" + self.baseJS.get("db_name")

        colnames = ["creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
        floatcols = [3, 4, 5, 6]
        fields = ["creator TEXT", "created TEXT", "modified TEXT", "lat REAL", "lon REAL", "lat_round STRING",
                  "lon_round STRING"]
        for i, feld in enumerate(self.baseJS.get("daten").get("felder")):
            name = feld.get("name")
            colnames.append(name)
            type = sqtype[feld.get("type")]
            if type == "REAL":
                floatcols.append(i)
            fields.append(name + " " + type)
        fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT REPLACE")
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_daten (" + ", ".join(fields) + ")"

        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute(stmt1)
        self.colnames["daten"] = colnames
        self.floatcols["daten"] = floatcols

        fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING",
                  "image_path STRING"]
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_images (" + ", ".join(fields) + ")"
        stmt2 = "CREATE INDEX IF NOT EXISTS latlonrnd_images ON " + self.tabellenname + "_images (lat_round, lon_round)";
        with conn:
            c = conn.cursor()
            c.execute(stmt1)
            c.execute(stmt2)
        self.colnames["images"] = ["creator", "created", "lat", "lon", "lat_round", "lon_round", "image_path"]
        self.floatcols["images"] = [3, 4, 5, 6]

        if self.baseJS.get("zusatz", None) is None:
            return
        colnames = ["nr", "creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
        floatcols = [4, 5, 6, 7]
        fields = ["nr INTEGER PRIMARY KEY", "creator TEXT", "created TEXT", "modified TEXT",
                  "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING"]
        for i, feld in enumerate(self.baseJS.get("zusatz").get("felder")):
            name = feld.get("name")
            colnames.append(name)
            type = sqtype[feld.get("type")]
            if type == "REAL":
                floatcols.append(i)
            fields.append(name + " " + type)
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_zusatz (" + ", ".join(fields) + ")"
        stmt2 = "CREATE INDEX IF NOT EXISTS latlonrnd_zusatz ON " + self.tabellenname + "_zusatz (lat_round, lon_round)";

        with conn:
            c = conn.cursor()
            c.execute(stmt1)
            c.execute(stmt2)
        self.colnames["zusatz"] = colnames
        self.floatcols["zusatz"] = floatcols

    def get_daten(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT * from " + self.tabellenname + "_daten WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))
            vals = c.fetchone()
            if vals is None:
                return None
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            return r

    def get_alle(self, kind):
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT * from " + self.tabellenname + "_" + kind)
            return c.fetchone()
            if vals is None:
                return None
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            return r

    def delete_daten(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("DELETE from " + self.tabellenname + "_daten WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))

    def update_daten(self, name, text, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        now = time.strftime("%Y.%m.%d %H:%M:%S")
        try:
            conn = self.getConn()
            with conn:
                c = conn.cursor()
                r1 = c.execute("UPDATE " + self.tabellenname + "_daten set "
                               + "creator = ?, modified = ?, "
                               + name + " = ? where lat_round = ? and lon_round = ?",
                               (self.aliasname, now, text, lat_round, lon_round))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"creator": self.aliasname, "created": now, "modified": now, "lat": lat, "lon": lon,
                            "lat_round": lat_round, "lon_round": lon_round}
                    felder = self.baseJS.get("daten").get("felder")
                    for feld in felder:
                        vals[feld.get("name")] = None
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute("INSERT INTO " + self.tabellenname + "_daten VALUES(" + ",".join(colnames) + ")", vals)
            self.app.add_marker(lat, lon)
        except Exception as e:
            utils.printEx("update_daten:", e)

    def insert_daten_from_osm(self, values):  # values = { [lat,lon]: properties }
        conn = self.getConn()
        colnames = self.colnames["daten"]
        # now = time.strftime("%Y.%m.%d %H:%M:%S")
        for value in values.items():
            lon = value[0][0]
            lat = value[0][1]
            lat_round = str(round(lat, self.stellen))
            lon_round = str(round(lon, self.stellen))
            value = value[1]

            vals = {}
            for feld in self.baseJS.get("daten").get("felder"):
                vals[feld.get("name")] = None
            vals["lat"] = lat
            vals["lon"] = lon
            vals["lat_round"] = lat_round
            vals["lon_round"] = lon_round
            vals["creator"] = "OSM"
            vals["created"] = "OSM"  # now
            vals["modified"] = "OSM"  # now
            vals.update(value)

            try:
                with conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO " + self.tabellenname + "_daten VALUES(" + ",".join(colnames) + ")", vals)
            except sqlite3.IntegrityError as e:
                print("duplicate", vals)
                utils.printEx("insert_daten_from_osm:", e)

    def get_zusatz(self, nr):
        conn = self.getConn()
        res = {}
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT * from " + self.tabellenname + "_zusatz WHERE nr = ?", (nr,))
            vals = c.fetchone()
            if vals is None:
                return None
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            return r

    def get_zusatz_numbers(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute(
                "SELECT nr from " + self.tabellenname + "_zusatz WHERE lat_round = ? and lon_round = ? ORDER BY nr",
                (lat_round, lon_round))
            res = [t[0] for t in r]
            return res

    def delete_zusatz(self, nr):
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("DELETE from " + self.tabellenname + "_zusatz WHERE nr = ?", (nr,))

    def update_zusatz(self, nr, name, text, lat, lon):
        now = time.strftime("%Y.%m.%d %H:%M:%S")
        rowid = nr
        try:
            conn = self.getConn()
            with conn:
                c = conn.cursor()
                if nr:
                    r1 = c.execute("UPDATE " + self.tabellenname + "_zusatz set "
                                   + "creator = ?, modified = ?, "
                                   + name + " = ? where nr = ?",
                                   (self.aliasname, now, text, nr))
                if not nr or r1.rowcount == 0:  # row did not yet exist
                    lat_round = str(round(lat, self.stellen))
                    lon_round = str(round(lon, self.stellen))
                    vals = {"nr": None, "creator": self.aliasname, "created": now, "modified": now, "lat": lat,
                            "lon": lon,
                            "lat_round": lat_round, "lon_round": lon_round}
                    for feld in self.baseJS.get("zusatz").get("felder"):
                        vals[feld.get("name")] = None
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute("INSERT INTO " + self.tabellenname + "_zusatz VALUES(" + ",".join(colnames) + ")", vals)
                    rowid = c.lastrowid
            self.app.add_marker(lat, lon)
            return rowid
        except Exception as e:
            utils.printEx("update_zusatz:", e)

    def get_images(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT image_path from " + self.tabellenname
                          + "_images WHERE lat_round = ? and lon_round = ?", (lat_round, lon_round))
            # r returns a list of tuples with one element "path"
            p = [t[0] for t in r]
            return p

    def insert_image(self, filename, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        now = time.strftime("%Y.%m.%d %H:%M:%S")
        try:
            conn = self.getConn()
            with conn:
                c = conn.cursor()

                fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING",
                          "lon_round STRING", "image_path STRING"]

                vals = {"creator": self.aliasname, "created": now, "lat": lat, "lon": lon,
                        "lat_round": lat_round, "lon_round": lon_round, "image_path": filename}
                colnames = [":" + k for k in vals.keys()]
                c.execute("INSERT INTO " + self.tabellenname + "_images VALUES(" + ",".join(colnames) + ")", vals)
            self.app.add_marker(lat, lon)
        except Exception as e:
            utils.printEx("insert_image:", e)

    def delete_images(self, lat, lon, image_path):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("DELETE from " + self.tabellenname +
                      "_images WHERE lat_round = ? and lon_round = ? and image_path=?",
                      (lat_round, lon_round, image_path))
            # print("deleted rows", c.rowcount)

    def getMarkerLocs(self, minlat, maxlat, minlon, maxlon):
        conn = self.getConn()
        minlat = str(round(minlat, self.stellen))
        maxlat = str(round(maxlat, self.stellen))
        minlon = str(round(minlon, self.stellen))
        maxlon = str(round(maxlon, self.stellen))
        with conn:
            c = conn.cursor()
            c.execute("SELECT lat, lon from " + self.tabellenname +
                      "_daten WHERE lat_round > ? and lat_round < ? and lon_round > ? and lon_round < ?",
                      (minlat, maxlat, minlon, maxlon))
            vals_daten = set(c.fetchall())
            c.execute("SELECT lat, lon from " + self.tabellenname +
                      "_images WHERE lat_round > ? and lat_round < ? and lon_round > ? and lon_round < ?",
                      (minlat, maxlat, minlon, maxlon))
            vals_images = set(c.fetchall())
            if self.baseJS.get("zusatz", None) is not None:
                c.execute("SELECT lat, lon from " + self.tabellenname +
                          "_zusatz WHERE lat_round > ? and lat_round < ? and lon_round > ? and lon_round < ?",
                          (minlat, maxlat, minlon, maxlon))
                vals_zusatz = set(c.fetchall())
            else:
                vals_zusatz = set()
            return vals_images.union(vals_daten).union(vals_zusatz)

    def existsImage(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT lat from " + self.tabellenname + "_images WHERE lat_round = ? and lon_round = ?",
                          (lat_round, lon_round))
            return len(list(r)) > 0

    def getRedYellowGreen(self, lat, lon):
        vals = self.get_daten(lat, lon)
        if vals is None:
            return None
        good = 0
        for f in ["abschließbar", "anlehnbar", "abstand", "ausparken", "geschützt"]:
            if vals[f]:
                good += 1
        if good == 5 and vals["zustand"] == "hoch":
            return "green"
        if good >= 2 and vals["zustand"] is not None and vals["zustand"] != "niedrig":
            return "yellow"
        return "red"

    def existsDatenOrZusatz(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT lat from " + self.tabellenname + "_daten WHERE lat_round = ? and lon_round = ?",
                          (lat_round, lon_round))
            if len(list(r)) > 0:
                return True
            if self.baseJS.get("zusatz", None) is not None:
                r = c.execute("SELECT lat from " + self.tabellenname + "_zusatz WHERE lat_round = ? and lon_round = ?",
                              (lat_round, lon_round))
                if len(list(r)) > 0:
                    return True
        return False

    def fillWith(self, values):
        conn = self.getConn()
        for sheet_name in values.keys():
            kind = sheet_name.split("_")[-1]  # daten, zusatz
            zusatz = kind == "zusatz"
            nrcols = len(self.colnames[kind])
            qmarks = ",".join(["?" for i in range(nrcols)])
            floatcols = self.floatcols[kind]
            vals = values[sheet_name]
            nulls = [None for i in range(nrcols)]
            # spreadsheet returns not full rows, and floats with a "," instead of a "."
            for row in vals:
                l = len(row)
                row.extend(nulls[0:nrcols - l])
                for i in floatcols:
                    row[i] = float(row[i].replace(",", "."))
                if zusatz:
                    row[0] = None

            with conn:
                r = conn.executemany("INSERT INTO " + sheet_name + " VALUES(" + qmarks + ")", vals)
                print(r)

    def getNewOrChanged(self, since):
        conn = self.getConn()
        result = {}
        with conn:
            c = conn.cursor()
            tabellenname = self.tabellenname + "_daten"
            r = c.execute("SELECT * FROM " + tabellenname + " WHERE creator = ? and modified like ? and modified > ?",
                          (self.aliasname, since[0:4] + "%", since))
            result[tabellenname] = r.fetchall()
            tabellenname = self.tabellenname + "_zusatz"
            r = c.execute("SELECT * FROM " + tabellenname + " WHERE creator = ? and modified like ? and modified > ?",
                          (self.aliasname, since[0:4] + "%", since))
            result[tabellenname] = r.fetchall()
        return result

# import config
# class App:
#     def __init__(self):
#         cfg = config.Config()
#         self.baseJS = cfg.getBase("Abstellanlagen")
#
#
# if __name__ == "__main__":
#     app = App()
#     dbinst = DB.instance()
#     dbinst.initDB(app)
#     dbinst.aliasname = "MUH"
#     laststored = "2020.01.01"
#     values = dbinst.getNewOrChanged(laststored)
#     print(values)
