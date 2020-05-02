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
        self.tabellenname = baseJS.get("db_tabellenname")
        self.stellen = baseJS.get("gps").get("nachkommastellen")
        db = utils.getDataDir() + "/" + baseJS.get("db_name")

        print("db path", db)
        self.conn = sqlite3.connect(db)

        fields = ["creator TEXT", "created TEXT", "modified TEXT", "lat REAL", "lon REAL", "lat_round STRING",
                  "lon_round STRING"]
        for feld in self.baseJS.get("felder"):
            fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
        fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT FAIL")
        stmt = "CREATE TABLE IF NOT EXISTS " + self.baseJS.get("db_tabellenname") + "_data (" + ", ".join(fields) + ")"
        with self.conn:
            c = self.conn.cursor()
            c.execute(stmt)

        fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING",
                  "image_path STRING"]
        stmt = "CREATE TABLE IF NOT EXISTS " + self.tabellenname + "_images (" + ", ".join(fields) + ")"
        with self.conn:
            c = self.conn.cursor()
            c.execute(stmt)

        fields = ["vorname TEXT", "nachname TEXT", "aliasname TEXT", "emailadresse TEXT"]
        stmt = "CREATE TABLE IF NOT EXISTS  account(" + ", ".join(fields) + ")"
        with self.conn:
            c = self.conn.cursor()
            c.execute(stmt)

    def getimages(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        p = []
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT image_path from " + self.tabellenname + "_images WHERE lat_round = ? and lon_round = ?",
                      (lat_round, lon_round))
            while True:
                r = c.fetchmany(100)
                if len(r) == 0:
                    break
                p.extend([t[0] for t in r])
            return p

    def getdata(self, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
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
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        now = time.strftime("%Y%m%d_%H%M%S")
        try:
            with self.conn:
                c = self.conn.cursor()
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

    def getMarkerLocs(self):
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT lat, lon from " + self.tabellenname + "_data")
            vals = c.fetchall()
            return vals

    def get_account(self):
        with self.conn:
            c = self.conn.cursor()
            c.execute("SELECT * from account")
            vals = c.fetchone()
            if vals is None:
                return {"vorname": "", "nachname": "", "aliasname": "", "emailadresse": ""}
            cols = [t[0] for t in c.description]
            r = dict(zip(cols, vals))
            self.aliasname = r["aliasname"]
            return r

    def update_account(self, name, text):
        try:
            with self.conn:
                c = self.conn.cursor()
                r1 = c.execute("UPDATE account set " + name + " = ?", (text,))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"vorname": "", "nachname": "", "aliasname": "", "emailadresse": ""}
                    vals[name] = text
                    colnames = [":" + k for k in vals.keys()]
                    c.execute("INSERT INTO account VALUES(" + ",".join(colnames) + ")", vals)
            if name == "aliasname":
                self.aliasname = text
        except Exception as e:
            utils.printEx("update_account:", e)

    def insert_image(self, filename, lat, lon):
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        now = time.strftime("%Y%m%d_%H%M%S")
        try:
            with self.conn:
                c = self.conn.cursor()

                fields = ["creator TEXT", "created TEXT", "lat REAL", "lon REAL", "lat_round STRING",
                          "lon_round STRING",
                          "image_path STRING"]

                vals = {"creator": self.aliasname, "created": now, "lat": lat, "lon": lon,
                        "lat_round": lat_round, "lon_round": lon_round, "image_path": filename}
                colnames = [":" + k for k in vals.keys()]
                c.execute("INSERT INTO " + self.tabellenname + "_images VALUES(" + ",".join(colnames) + ")", vals)
        except Exception as e:
            utils.printEx("insert_image:", e)
