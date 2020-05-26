# https://developers.google.com/sheets/api/quickstart/python

# sheets v4 and drive v3 seen here:
# https://www.googleapis.com/discovery/v1/apis/

import os
import pickle
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config
import utils

SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/photoslibrary',
          'https://www.googleapis.com/auth/photoslibrary.sharing',
          'https://www.googleapis.com/auth/userinfo.profile']


def pyinst(path):
    path = path.strip()
    if os.path.exists(path):
        return path
    if hasattr(sys, "_MEIPASS"):  # i.e. if running as exe produced by pyinstaller
        pypath = sys._MEIPASS + "/" + path
        if os.path.exists(pypath):
            return pypath
    return path


class Google:
    def __init__(self):
        print("Google init")
        pass

    def getCreds(self):
        """Calls the Apps Script API.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    pyinst('credentials.json'), SCOPES)
                creds = flow.run_local_server(port=53876)

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def get_user_info(self, creds):
        """Send a request to the UserInfo API to retrieve the user's information.
        Args:
          credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                       request.
        Returns:
          User information as a dict.
        """

        user_info_service = build('oauth2', 'v2', credentials=creds)
        try:
            user_info = user_info_service.userinfo().get().execute()
            if user_info and user_info.get('id'):
                return user_info
        except Exception as e:
            utils.printEx('cannot get user info', e)
        return None
        # {
        #     'id': '101083883722235859400',
        #     'name': 'Michael Uhlenberg ADFC München',
        #     'given_name': 'Michael',
        #     'family_name': 'Uhlenberg ADFC München',
        #     'picture': 'https://lh3.googleusercontent.com/a-/AOh14GgUHWrbCrmA4YLp1fHYBKrRexZDWfC96h09dNze5w',
        #     'locale': 'de'
        # }


class GSheet(Google):
    def __init__(self, app):
        self.app = app
        self.baseJS = app.baseJS
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")

        self.getSSheet()
        self.spreadsheet_id = self.baseJS.get("spreadsheet_id")
        sheet_basename = self.baseJS.get("db_tabellenname")  # gleicher Name wie DB
        self.sheet_names = [sheet_basename + "_daten", sheet_basename + "_images"]
        if self.baseJS.get("zusatz") is not None:
            self.sheet_names.append(sheet_basename + "_zusatz")

        self.ist_headers = {}
        self.soll_headers = {}
        self.checkSheets()

        for sheet_name in self.sheet_names:
            try:
                headers = self.ssheet.values().get(spreadsheetId=self.spreadsheet_id,
                                                   range=sheet_name + "!1:1").execute().get('values', [])
                self.ist_headers[sheet_name] = headers if len(headers) == 0 else headers[0]
            except Exception as e:
                utils.printEx("Kann Arbeitsblatt " + self.spreadsheet_id + "/" + sheet_name + " nicht laden", e)
                raise (e)

        self.checkColumns()

    # get service more often than necessary for fear of expiring credentials
    def getSSheet(self):
        creds = self.getCreds()
        serviceSH = build('sheets', 'v4', credentials=creds)
        self.ssheet = serviceSH.spreadsheets()

    def checkSheets(self):
        sheet_props = self.ssheet.get(spreadsheetId=self.spreadsheet_id, fields="sheets.properties").execute()
        sheet_names_exi = [sheet_prop["properties"]["title"] for sheet_prop in sheet_props["sheets"]]
        print("Existing sheets", sheet_names_exi)
        for sheet_name in self.sheet_names:
            kind = sheet_name.split("_")[-1]  # daten, zusatz
            if kind == "daten":
                names = ["creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
            elif kind == "images":
                names = ["creator", "created", "lat", "lon", "lat_round", "lon_round", "image_path", "image_url"]
            elif kind == "zusatz":
                names = ["nr", "creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"]
            if kind != "images":
                names.extend([feld.get("name") for feld in self.baseJS.get(kind).get("felder")])
            self.soll_headers[sheet_name] = names
            if sheet_name not in sheet_names_exi:
                self.addSheet(sheet_name, len(self.soll_headers[sheet_name]) + 5)  # some reserve for future fields

    def addSheet(self, sheet_name, nrCols):
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'sheetType': 'GRID',
                        'gridProperties': {
                            # 'rowCount': rows,
                            'columnCount': nrCols,
                        }
                    }
                }
            }]
        }
        result = self.ssheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
        properties = result['replies'][0]['addSheet']['properties']
        print("added sheet props", properties)

    def checkColumns(self):
        # Prüfen ob im sheet die Felder angelegt sind
        for sheet_name in self.sheet_names:
            for name in self.soll_headers[sheet_name]:
                if not name in self.ist_headers[sheet_name]:
                    self.addColumn(sheet_name, name)
                    self.ist_headers[sheet_name].append(name)

    def addColumn(self, sheet_name, colName):
        l = len(self.ist_headers[sheet_name])
        print("addColumn", l, colName)
        self.addValue(sheet_name, 0, l, colName);

    def addValue(self, sheet_name, row, col, val):
        # row, col are 0 based
        values = [[val]]
        body = {"values": values}
        range = sheet_name + "!" + chr(ord('A') + col) + str(row + 1)  # 0,0-> A1, 1,2->C2 2,1->B3
        result = self.ssheet.values().update(spreadsheetId=self.spreadsheet_id, range=range, valueInputOption="RAW",
                                             body=body).execute()
        print("addValue", result)

    def appendValues(self, sheet_name, values):
        self.getSSheet()
        body = {
            "majorDimension": "ROWS",
            "values": values
        }
        result = self.ssheet.values().append(spreadsheetId=self.spreadsheet_id, range=sheet_name,
                                             valueInputOption="RAW",
                                             body=body).execute()
        print("appendValue result:", result)

    def getValues(self, sheet_name, a1range=""):
        self.getSSheet()
        result = self.ssheet.values().get(spreadsheetId=self.spreadsheet_id,
                                          range=sheet_name + a1range).execute().get('values', [])
        print("getValues", sheet_name, a1range, result[0:3])
        return result

    def column_range(self, sheet_name, hdr1, hdr2):
        x1 = self.ist_headers[sheet_name].index(hdr1)
        x2 = self.ist_headers[sheet_name].index(hdr2)
        if x1 > x2:
            x1, x2 = x2, x1
        assert (x2 < 26)
        range = "!" + chr(ord('A') + x1) + ":" + chr(ord('A') + x2)
        return range

    def batchget(self, ranges):
        self.getSSheet()
        result = self.ssheet.values().batchGet(spreadsheetId=self.spreadsheet_id,
                                               ranges=ranges).execute().get('valueRanges', [])
        result = [r.get("values")[0] for r in result]
        print("batchget", ranges[0:3], result[0:3])
        return result

    def getValuesWithin(self, minlat, maxlat, minlon, maxlon):
        self.getSSheet()
        minlat = str(round(minlat, self.stellen)).replace(".", ",")
        maxlat = str(round(maxlat, self.stellen)).replace(".", ",")
        minlon = str(round(minlon, self.stellen)).replace(".", ",")
        maxlon = str(round(maxlon, self.stellen)).replace(".", ",")
        ret = {}
        for sheet_name in self.sheet_names:
            # assume that lat_round and lon_round are adjacent, so that values is a list of 2-tuples
            range = self.column_range(sheet_name, "lat_round", "lon_round")
            values = self.getValues(sheet_name, range)
            ranges = [sheet_name + "!" + str(i + 1) + ":" + str(i + 1) for i, v in enumerate(values) if
                      minlat < v[0] < maxlat and minlon < v[1] < maxlon]
            values = self.batchget(ranges)
            ret[sheet_name] = values
        return ret

    def insert_daten_from_osm(self, osmvalues):  # values = { [lat,lon]: properties }
        values = []
        for osmvalue in osmvalues.items():
            lon = osmvalue[0][0]
            lat = osmvalue[0][1]
            lat_round = str(round(lat, self.stellen))
            lon_round = str(round(lon, self.stellen))
            osmvalue = osmvalue[1]

            row = [None for i in range(20)]
            row[0] = "OSM"
            row[1] = "OSM"
            row[2] = "OSM"
            row[3] = lat
            row[4] = lon
            row[5] = lat_round
            row[6] = lon_round
            row[7] = osmvalue.get("ort", None)
            row[9] = osmvalue.get("anzahl", None)
            row[17] = osmvalue.get("geschützt", None)
            row[19] = osmvalue.get("bemerkung", None)
            values.append(row)
        self.appendValues("osm", values)


class App:
    def __init__(self):
        cfg = config.Config()
        self.baseJS = cfg.getBase("Abstellanlagen")


def testSheet(app):
    gsheet = GSheet(app)
    # gsheet.checkSheets()

    # dbinst = db.DB.instance()
    # dbinst.initDB(app)
    for sheet_name in gsheet.sheet_names:
        kind = sheet_name.split("_")[-1]  # daten, zusatz
        # values = dbinst.get_alle(kind)

        # values = [["MUH", "OSM", "OSM", 48.1412437, 11.5594636, "48.14124", "11.55946"]]
        # values = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
        # gsheet.appendValues(sheet_name, values)

        range = gsheet.column_range(sheet_name, "lat_round", "lon_round")
        values = gsheet.getValues(sheet_name, range)
        print("values", values)


if __name__ == "__main__":
    app = App()
    testSheet(app)
