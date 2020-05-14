# https://developers.google.com/sheets/api/quickstart/python
# https://developers.google.com/photos/library/reference/rest/v1/mediaItems

# sheets v4 and drive v3 seen here:
# https://www.googleapis.com/discovery/v1/apis/

import os
import pickle
import sys

from google_auth_httplib2 import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import utils

SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file']


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
    def __init__(self):
        pass

    def getSheet(self):
        print("1getSheet")
        self.spreadSheetId = "1xRwSYtnmB4Y3_2f8ZPHxLuzMy7WuuZIW8jOY0nsIzN8"  # RFS_0AXX Backend
        self.spreadSheetName = "RFS_0AXX Backend"

        creds = self.getCreds()
        print("2getSheet")
        serviceSH = build('sheets', 'v4', credentials=creds)
        print("3getSheet")
        serviceDR = build('drive', 'v3', credentials=creds)
        print("4getSheet")
        self.ssheet = serviceSH.spreadsheets()
        sheet_props = self.ssheet.get(spreadsheetId=self.spreadSheetId, fields="sheets.properties").execute()
        print("5getSheet")
        sheet_names = [sheet_prop["properties"]["title"] for sheet_prop in sheet_props["sheets"]]
        print("6getDrive")
        print(sheet_names)

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
        #get
        print(self.about.get().execute())
        self.teamdrives = serviceDR.teamdrives()
        print("teamdrives", dir(self.teamdrives))
        print(self.teamdrives.list().execute())
        #'create', 'delete', 'get', 'list', 'list_next', 'update']

        print("")

GDrive().getDrive()