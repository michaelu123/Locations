import sqlite3

import utils

sqtype = {"int": "INTEGER", "string": "TEXT", "float": "REAL"}

def initDB(baseJS):
    db = utils.getDataDir() + "/" + baseJS.get("db_name")

    print("db path", db)
    conn = sqlite3.connect(db)

    fields = ["benutzer TEXT", "datum TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING"]
    for feld in baseJS.get("felder"):
        fields.append(feld.get("name") + " " + sqtype[feld.get("type")])
    fields.append("PRIMARY KEY (lat_round, lon_round) ON CONFLICT FAIL")
    stmt = "CREATE TABLE " + baseJS.get("db_tabellenname") + "_data (" + ",".join(fields) + ")"
    c = conn.cursor()
    try:
        with conn:
            c.execute(stmt)
    except sqlite3.OperationalError:
        pass

    fields = ["benutzer TEXT", "datum TEXT", "lat REAL", "lon REAL", "lat_round STRING", "lon_round STRING", "image_path STRING"]
    stmt = "CREATE TABLE IF NOT EXISTS " + baseJS.get("db_tabellenname") + "_images (" + ",".join(fields) + ")"
    c = conn.cursor()
    try:
        with conn:
            c.execute(stmt)
    except sqlite3.OperationalError:
        pass
