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
        db = utils.getDataDir() + "/" + self.baseJS.get("db_name")

        fields = ["creator TEXT", "created TEXT", "modified TEXT", "lat REAL", "lon REAL", "lat_round STRING",
                  "lon_round STRING"]
        for feld in self.baseJS.get("daten").get("felder"):
            fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
        fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT FAIL")
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_data (" + ", ".join(fields) + ")"

        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute(stmt1)

        fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING",
                  "image_path STRING"]
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_images (" + ", ".join(fields) + ")"
        stmt2 = "CREATE INDEX IF NOT EXISTS latlonrnd_images ON " + self.tabellenname + "_images (lat_round, lon_round)";
        with conn:
            c = conn.cursor()
            c.execute(stmt1)
            c.execute(stmt2)

        if self.baseJS.get("zusatz", None) is None:
            return
        fields = ["nr INTEGER PRIMARY KEY", "creator TEXT", "created TEXT", "modified TEXT",
                  "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING"]
        for feld in self.baseJS.get("zusatz").get("felder"):
            fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
        stmt1 = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_zusatz (" + ", ".join(fields) + ")"
        stmt2 = "CREATE INDEX IF NOT EXISTS latlonrnd_zusatz ON " + self.tabellenname + "_zusatz (lat_round, lon_round)";

        with conn:
            c = conn.cursor()
            c.execute(stmt1)
            c.execute(stmt2)

    def get_data(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT * from " + self.tabellenname + "_data WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))
            vals = c.fetchone()
            if vals is None:
                return None
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            return r

    def delete_data(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("DELETE from " + self.tabellenname + "_data WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))

    def update_data(self, name, text, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        now = time.strftime("%Y.%m.%d %H:%M:%S")
        try:
            conn = self.getConn()
            with conn:
                c = conn.cursor()
                r1 = c.execute("UPDATE " + self.tabellenname + "_data set "
                               + "modified = ?, "
                               + name + " = ? where lat_round = ? and lon_round = ?",
                               (now, text, lat_round, lon_round))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"creator": self.aliasname, "created": now, "modified": now, "lat": lat, "lon": lon,
                            "lat_round": lat_round, "lon_round": lon_round}
                    felder = self.baseJS.get("daten").get("felder")
                    for feld in felder:
                        vals[feld.get("name")] = None
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute("INSERT INTO " + self.tabellenname + "_data VALUES(" + ",".join(colnames) + ")", vals)
            self.app.add_marker(lat, lon)
        except Exception as e:
            utils.printEx("update_data:", e)

    def insert_data_from_osm(self, values):  # values = { [lat,lon]: properties }
        conn = self.getConn()
        try:
            with conn:
                c = conn.cursor()
                # just to get the column names...
                r = c.execute("SELECT * from " + self.tabellenname + "_data WHERE lat_round=0 and lon_round=0")
                c.fetchone()
                colnames = [":" + t[0] for t in c.description]
        except Exception as e:
            utils.printEx("insert_data_from_osm:", e)

        #now = time.strftime("%Y.%m.%d %H:%M:%S")
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
            vals["created"] = "OSM" #now
            vals["modified"] = "OSM" #now
            vals.update(value)

            try:
                with conn:
                    c = conn.cursor()
                    c.execute("INSERT INTO " + self.tabellenname + "_data VALUES(" + ",".join(colnames) + ")", vals)
            except sqlite3.IntegrityError as e:
                print("duplicate", vals)
                utils.printEx("insert_data_from_osm:", e)

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
                                   + "modified = ?, "
                                   + name + " = ? where nr = ?",
                                   (now, text, nr))
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

    def getMarkerLocs(self):
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT lat_round, lon_round from " + self.tabellenname + "_data")
            vals_data = set(c.fetchall())
            c.execute("SELECT lat_round, lon_round from " + self.tabellenname + "_images")
            vals_images = set(c.fetchall())
            c.execute("SELECT lat_round, lon_round from " + self.tabellenname + "_zusatz")
            vals_zusatz = set(c.fetchall())
            return vals_images.union(vals_data).union(vals_zusatz)

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
        vals = self.get_data(lat, lon)
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

    def existsDataOrZusatz(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT lat from " + self.tabellenname + "_data WHERE lat_round = ? and lon_round = ?",
                          (lat_round, lon_round))
            if len(list(r)) > 0:
                return True
            r = c.execute("SELECT lat from " + self.tabellenname + "_zusatz WHERE lat_round = ? and lon_round = ?",
                          (lat_round, lon_round))
            if len(list(r)) > 0:
                return True
        return False
