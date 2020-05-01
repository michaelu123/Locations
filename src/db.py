import sqlite3
import time

import utils

sqtype = {"int": "INTEGER", "string": "TEXT", "float": "REAL"}
nullval = {"int": 0, "string": "", "float": 0.0}


class DB():
    _dbinst = None

    @staticmethod
    def instance():
        if DB._dbinst is None:
            DB._dbinst = DB()
        return DB._dbinst

    def initDB(self, baseJS, app):
        self.baseJS = baseJS
        self.app = app
        db = utils.getDataDir() + "/" + baseJS.get("db_name")

        print("db path", db)
        self.conn = sqlite3.connect(db)

        fields = ["benutzer TEXT", "datum TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING"]
        for feld in baseJS.get("felder"):
            fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
        fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT FAIL")
        stmt = "CREATE TABLE " + baseJS.get("db_tabellenname") + "_data (" + ", ".join(fields) + ")"
        c = self.conn.cursor()
        try:
            with self.conn:
                c.execute(stmt)
        except sqlite3.OperationalError:
            pass

        self.tabellenname = baseJS.get("db_tabellenname")
        fields = ["benutzer TEXT", "datum TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING",
                  "image_path STRING"]
        stmt = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_images (" + ", ".join(fields) + ")"
        c = self.conn.cursor()
        try:
            with self.conn:
                c.execute(stmt)
        except sqlite3.OperationalError:
            pass

    def getimages(self, lat, lon):
        stellen = self.baseJS.get("gps").get("nachkommastellen")
        lat_round = str(round(lat, stellen))
        lon_round = str(round(lon, stellen))
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT image_path from " + self.tabellenname + "_images WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))
            r = c.fetchmany()
            return r or []

    def getdata(self, lat, lon):
        stellen = self.baseJS.get("gps").get("nachkommastellen")
        lat_round = str(round(lat, stellen))
        lon_round = str(round(lon, stellen))
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT * from " + self.tabellenname + "_data WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))
            vals = c.fetchone()
            if vals is None:
                return None
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            return r

    def update_data(self, name, text, lat, lon):
        stellen = self.baseJS.get("gps").get("nachkommastellen")
        lat_round = str(round(lat, stellen))
        lon_round = str(round(lon, stellen))
        try:
            with self.conn:
                c = self.conn.cursor()
                r1 = c.execute("UPDATE " + self.tabellenname + "_data set "
                               + name + " = ? where lat_round = ? and lon_round = ?",
                               (text, lat_round, lon_round))
                if r1.rowcount == 0:  # row did not yet exist
                    now = time.strftime("%Y%m%d_%H%M%S")
                    vals = {"benutzer": "MUH", "datum": now, "lat": lat, "lon": lon, "lat_round":
                        lat_round, "lon_round": lon_round}
                    for feld in self.baseJS.get("felder"):
                        vals[feld.get("name")] = nullval[feld.get("type")]
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute(
                        "INSERT INTO " + self.tabellenname + "_data VALUES(" + ",".join(colnames) + ")",
                        vals)
            self.app.add_marker(lat, lon)

        except Exception as e:
            utils.printEx("update_data:", e)

    def getMarkerLocs(self):
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT lat, lon from " + self.tabellenname + "_data")
            vals = c.fetchall()
            return vals

