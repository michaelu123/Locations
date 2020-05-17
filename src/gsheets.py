# https://developers.google.com/sheets/api/quickstart/python
# https://developers.google.com/photos/library/reference/rest/v1/mediaItems

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
        self.spreadsheet_id = self.baseJS.get("spreadsheet_id")
        sheet_basename = self.baseJS.get("db_tabellenname")  # gleicher Name wie DB
        self.sheet_names = [sheet_basename + "_daten"]
        self.ist_headers = {}
        self.soll_headers = {}
        if self.baseJS.get("zusatz") is not None:
            self.sheet_names.append(sheet_basename + "_zusatz")

    def checkSheets(self):
        print("1getSheet")
        creds = self.getCreds()
        print("2getSheet")
        serviceSH = build('sheets', 'v4', credentials=creds)
        print("3getSheet")
        serviceDR = build('drive', 'v3', credentials=creds)
        print("4getSheet")
        self.ssheet = serviceSH.spreadsheets()
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

        for sheet_name in self.sheet_names:
            try:
                headers = self.ssheet.values().get(spreadsheetId=self.spreadsheet_id,
                                                   range=sheet_name + "!1:1").execute().get('values', [])
                self.ist_headers[sheet_name] = headers if len(headers) == 0 else headers[0]
            except Exception as e:
                utils.printEx("Kann Arbeitsblatt " + self.spreadsheet_id + "/" + sheet_name + " nicht laden", e)
                raise (e)
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

    def addValue(self, sheetName, row, col, val):
        # row, col are 0 based
        values = [[val]]
        body = {"values": values}
        range = sheetName + "!" + chr(ord('A') + col) + str(row + 1)  # 0,0-> A1, 1,2->C2 2,1->B3
        result = self.ssheet.values().update(spreadsheetId=self.spreadsheet_id, range=range, valueInputOption="RAW",
                                             body=body).execute()
        print("result2", result)


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
    gsheet.checkSheets()
