import sqlite3
import utils


def initDB():
    db = utils.getDataDir() + "/Abstellanlagen.db"

    print("db path", db)
    conn = sqlite3.connect(db)

    # c = conn.cursor()
    # try:
    #     with conn:
    #         c.execute("""CREATE TABLE arbeitsblatt(
    #         tag TEXT,
    #         fnr INTEGER,
    #         einsatzstelle TEXT,
    #         beginn TEXT,
    #         ende TEXT,
    #         fahrtzeit TEXT,
    #         mvv_euro TEXT,
    #         kh INTEGER)
    #         """)
    # except OperationalError:
    #     pass
    # try:
    #     with conn:
    #         c.execute("""CREATE TABLE eigenschaften(
    #         vorname TEXT,
    #         nachname TEXT,
    #         wochenstunden TEXT,
    #         emailadresse TEXT)
    #         """)
    # except OperationalError:
    #     pass
    # try:
    #     with conn:
    #         c.execute("""delete from arbeitsblatt where einsatzstelle="" and beginn="" and ende="" """)
    # except OperationalError:
    pass
