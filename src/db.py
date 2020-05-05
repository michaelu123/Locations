import sqlite3
import time
import threading
import utils

sqtype = {"int": "INTEGER", "string": "TEXT", "float": "REAL"}
nullval = {"int": 0, "string": "", "float": 0.0}
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
        for feld in self.baseJS.get("felder"):
            fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
        fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT FAIL")
        stmt = "CREATE TABLE IF NOT EXISTS " + self.baseJS.get("db_tabellenname") + "_data (" + ", ".join(fields) + ")"

        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute(stmt)

        fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING",
                  "image_path STRING"]
        stmt = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_images (" + ", ".join(fields) + ")"
        with conn:
            c = conn.cursor()
            c.execute(stmt)

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
        now = time.strftime("%Y%m%d_%H%M%S")
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
                    for feld in self.baseJS.get("felder"):
                        vals[feld.get("name")] = nullval[feld.get("type")]
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute("INSERT INTO " + self.tabellenname + "_data VALUES(" + ",".join(colnames) + ")", vals)
                    self.app.add_marker(lat, lon)
        except Exception as e:
            utils.printEx("update_data:", e)

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
        now = time.strftime("%Y%m%d_%H%M%S")
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
                      "_images WHERE lat_round = ? and lon_round = ? and image_path=?", (lat_round, lon_round, image_path))
            # print("deleted rows", c.rowcount)

    def getMarkerLocs(self):
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            c.execute("SELECT lat, lon from " + self.tabellenname + "_data")
            vals_data = set(c.fetchall())
            c.execute("SELECT lat, lon from " + self.tabellenname + "_images")
            vals_images = set(c.fetchall())
            return vals_data.union(vals_images)

    def existsLatLon(self, lat, lon):
        conn = self.getConn()
        with conn:
            c = conn.cursor()
            r = c.execute("SELECT lat from " + self.tabellenname + "_data WHERE lat = ? and lon = ?", (lat, lon))
            if len(list(r)) > 0:
                return True
            r = c.execute("SELECT lat from " + self.tabellenname + "_images WHERE lat = ? and lon = ?", (lat, lon))
            if len(list(r)) > 0:
                return True
            return False