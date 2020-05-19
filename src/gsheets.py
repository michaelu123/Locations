# https://developers.google.com/sheets/api/quickstart/python
# https://developers.google.com/photos/library/reference/rest/v1/mediaItems

# Using Google Spreadsheets as a Database in the Cloud
# https://www.youtube.com/watch?v=rWCLROPKug0

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

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']


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
        print("1getCreds")
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        print("2getCreds")
        if not creds or not creds.valid:
            print("3getCreds")
            if creds and creds.expired and creds.refresh_token:
                print("4getCreds")
                creds.refresh(Request())
                print("5getCreds")
            else:
                print("6getCreds")
                flow = InstalledAppFlow.from_client_secrets_file(
                    pyinst('credentials.json'), SCOPES)
                print("7getCreds")
                creds = flow.run_local_server(port=53876)

            print("8getCreds")
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                print("9getCreds")
                pickle.dump(creds, token)
        print("10getCreds")
        return creds


class GSheet(Google):
    def __init__(self, app):
        self.app = app
        self.baseJS = app.baseJS
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")

        creds = self.getCreds()
        serviceSH = build('sheets', 'v4', credentials=creds)
        # serviceDR = build('drive', 'v3', credentials=creds)
        self.ssheet = serviceSH.spreadsheets()

        self.spreadsheet_id = self.baseJS.get("spreadsheet_id")
        sheet_basename = self.baseJS.get("db_tabellenname")  # gleicher Name wie DB
        self.sheet_names = [sheet_basename + "_daten"]
        if self.baseJS.get("zusatz") is not None:
            self.sheet_names.append(sheet_basename + "_zusatz")

        self.ist_headers = {}
        self.soll_headers = {}
        for sheet_name in self.sheet_names:
            try:
                headers = self.ssheet.values().get(spreadsheetId=self.spreadsheet_id,
                                                   range=sheet_name + "!1:1").execute().get('values', [])
                self.ist_headers[sheet_name] = headers if len(headers) == 0 else headers[0]
            except Exception as e:
                utils.printEx("Kann Arbeitsblatt " + self.spreadsheet_id + "/" + sheet_name + " nicht laden", e)
                raise (e)

    def checkSheets(self):
        sheet_props = self.ssheet.get(spreadsheetId=self.spreadsheet_id, fields="sheets.properties").execute()
        print("5getSheet")
        sheet_names_exi = [sheet_prop["properties"]["title"] for sheet_prop in sheet_props["sheets"]]
        print("6getDrive")
        print(sheet_names_exi)
        for sheet_name in self.sheet_names:
            kind = sheet_name.split("_")[-1]  # daten, zusatz
            names = ["nr"] if kind == "zusatz" else []
            names.extend(["creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"])
            names.extend([feld.get("name") for feld in self.baseJS.get(kind).get("felder")])
            self.soll_headers[sheet_name] = names
            if sheet_name not in sheet_names_exi:
                self.addSheet(sheet_name, len(self.soll_headers[sheet_name]))

        self.checkColumns()

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
        print("props", properties)

    def checkColumns(self):
        # Prüfen ob im sheet die Felder angelegt sind
        for sheet_name in self.sheet_names:
            for name in self.soll_headers[sheet_name]:
                if not name in self.ist_headers[sheet_name]:
                    self.addColumn(sheet_name, name)
                    self.ist_headers[sheet_name].append(name)

    def addColumn(self, sheet_name, colName):
        l = len(self.ist_headers[sheet_name])
        self.addValue(sheet_name, 0, l, colName);

    def addValue(self, sheet_name, row, col, val):
        # row, col are 0 based
        values = [[val]]
        body = {"values": values}
        range = sheet_name + "!" + chr(ord('A') + col) + str(row + 1)  # 0,0-> A1, 1,2->C2 2,1->B3
        result = self.ssheet.values().update(spreadsheetId=self.spreadsheet_id, range=range, valueInputOption="RAW",
                                             body=body).execute()
        print("result2", result)

    def appendValues(self, sheet_name, values):
        body = {
            "majorDimension": "ROWS",
            "values": values
        }
        result = self.ssheet.values().append(spreadsheetId=self.spreadsheet_id, range=sheet_name,
                                             valueInputOption="RAW",
                                             body=body).execute()
        print("result3", result)

    def getValues(self, sheet_name, a1range=""):
        result = self.ssheet.values().get(spreadsheetId=self.spreadsheet_id,
                                          range=sheet_name + a1range).execute().get('values', [])
        print("result4", result)
        return result

    def column_range(self, sheet_name, hdr1, hdr2):
        x1 = self.ist_headers[sheet_name].index(hdr1)
        x2 = self.ist_headers[sheet_name].index(hdr2)
        if x1 > x2:
            x1, x2 = x2, x1
        range = "!" + chr(ord('A') + x1) + ":" + chr(ord('A') + x2)
        return range

    def batchget(self, ranges):
        result = self.ssheet.values().batchGet(spreadsheetId=self.spreadsheet_id,
                                          ranges=ranges).execute().get('valueRanges', [])
        result = [ r.get("values")[0] for r in result]
        print("result4", result)
        return result


    def getValuesWithin(self, minlat, maxlat, minlon, maxlon):
        minlat = str(round(minlat, self.stellen)).replace(".", ",")
        maxlat = str(round(maxlat, self.stellen)).replace(".", ",")
        minlon = str(round(minlon, self.stellen)).replace(".", ",")
        maxlon = str(round(maxlon, self.stellen)).replace(".", ",")
        ret = {}
        for sheet_name in self.sheet_names:
            # assume that lat_round and lon_round are adjacent, so that values is a list of 2-tuples
            range = self.column_range(sheet_name, "lat_round", "lon_round")
            values = self.getValues(sheet_name, range)
            ranges = [sheet_name + "!" +str(i+1)+":"+str(i+1) for i,v in enumerate(values) if minlat < v[0] < maxlat and minlon < v[1] < maxlon]
            values = self.batchget(ranges)
            ret[sheet_name] = values
        return ret


class GDrive(Google):
    def __init__(self):
        pass

    def getDrive(self):
        print("1getDrive")
        creds = self.getCreds()
        print("2getDrive")
        serviceDR = build('drive', 'v3', credentials=creds)
        # dir(serviceDR):
        #  'about', 'changes', 'channels', 'comments', 'drives', 'files',
        #  'new_batch_http_request', 'permissions', 'replies', 'revisions', 'teamdrives'
        print("3getDrive")
        self.about = serviceDR.about()
        print("about", dir(self.about))
        # get
        print(self.about.get().execute())
        self.teamdrives = serviceDR.teamdrives()
        print("teamdrives", dir(self.teamdrives))
        print(self.teamdrives.list().execute())
        # 'create', 'delete', 'get', 'list', 'list_next', 'update']

        print("")

class App:
    def __init__(self):
        cfg = config.Config()
        self.baseJS = cfg.getBase("Abstellanlagen")


if __name__ == "__main__":
    app = App()
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
