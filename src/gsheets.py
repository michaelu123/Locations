# https://developers.google.com/sheets/api/quickstart/python
# https://developers.google.com/photos/library/reference/rest/v1/mediaItems
# https://developers.google.com/photos/library/guides/access-media-items

# sheets v4 and drive v3 seen here:
# https://www.googleapis.com/discovery/v1/apis/

# https://stackoverflow.com/questions/50573196/access-google-photo-api-with-python-using-google-api-python-client
import os
import pickle
import sys

from google.auth.transport.requests import Request, AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config
import utils

#          'https://www.googleapis.com/auth/drive.file',
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/photoslibrary']


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


class GSheet(Google):
    def __init__(self, app):
        self.app = app
        self.baseJS = app.baseJS
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")

        creds = self.getCreds()
        serviceSH = build('sheets', 'v4', credentials=creds)
        self.ssheet = serviceSH.spreadsheets()

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

    def checkSheets(self):
        sheet_props = self.ssheet.get(spreadsheetId=self.spreadsheet_id, fields="sheets.properties").execute()
        sheet_names_exi = [sheet_prop["properties"]["title"] for sheet_prop in sheet_props["sheets"]]
        print(sheet_names_exi)
        for sheet_name in self.sheet_names:
            kind = sheet_name.split("_")[-1]  # daten, zusatz
            names = ["nr"] if kind == "zusatz" else []
            names.extend(["creator", "created", "modified", "lat", "lon", "lat_round", "lon_round"])
            if kind == "images":
                names.append("image_path")
            else:
                names.extend([feld.get("name") for feld in self.baseJS.get(kind).get("felder")])
            self.soll_headers[sheet_name] = names
            if sheet_name not in sheet_names_exi:
                self.addSheet(sheet_name, len(self.soll_headers[sheet_name]))

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
        print("addColumn", l, colName)
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
        assert (x2 < 26)
        range = "!" + chr(ord('A') + x1) + ":" + chr(ord('A') + x2)
        return range

    def batchget(self, ranges):
        result = self.ssheet.values().batchGet(spreadsheetId=self.spreadsheet_id,
                                               ranges=ranges).execute().get('valueRanges', [])
        result = [r.get("values")[0] for r in result]
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


class GPhoto(Google):
    def __init__(self):
        self.app = app
        self.baseJS = app.baseJS
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")
        creds = self.getCreds()
        self.servicePH = build('photoslibrary', 'v1', credentials=creds)

        # print("pl", dir(self.servicePH))
        # # ['albums', 'mediaItems','new_batch_http_request', 'sharedAlbums']
        # print("al", dir(self.servicePH.albums()))
        # # 'addEnrichment', 'batchAddMediaItems', 'batchRemoveMediaItems', 'create', 'get', 'list', 'list_next', 'share', 'unshare']
        # print("mi", dir(self.servicePH.mediaItems()))
        # # ['batchCreate', 'batchGet', 'get', 'list', 'list_next', 'search', 'search_next']
        # print("bc", dir(self.servicePH.mediaItems().batchCreate()))
        # # ['add_response_callback', 'body', 'body_size', 'execute', 'from_json', 'headers',
        # # 'http', 'method', 'methodId', 'next_chunk', 'postproc', 'response_callbacks', 'resumable',
        # # 'resumable_progress', 'resumable_uri', 'to_json', 'uri'

        self.album_name = self.baseJS.get("db_tabellenname")  # use also as album name
        self.album_id = self.create_or_retrieve_album()

    def getAlbums(self):
        # Call the Photo v1 API
        results = self.servicePH.albums().list(
            pageSize=10, fields="nextPageToken,albums(id,title)").execute()
        items = results.get('albums', [])
        return items

    def create_or_retrieve_album(self):
        # Find albums to see if one matches album_title
        for a in self.getAlbums():
            if a["title"] == self.album_name:
                album_id = a["id"]
                return album_id
        # No matches, create new album
        create_album_body = {"album": {"title": self.album_name}}
        resp = self.servicePH.albums().create(body=create_album_body).execute()
        if "id" in resp:
            return resp['id']
        else:
            raise RuntimeError(
                "Could not create photo album '\{0}\'. Server Response: {1}".format(self.album_name, resp))

    # from https://github.com/eshmu/gphotos-upload
    # or https://learndataanalysis.org/upload-media-items-google-photos-api-and-python-part-4/
    # photo_objs = { "filepath": path, "desc": description }
    # we add "token": uploadtoken, "id": mediaItemId
    # Achtung: Es gibt ein Limit von 20000 Photos pro Album!
    def upload_photos(self, photo_objs):
        self.session = AuthorizedSession(self.getCreds())
        # interrupt upload if an upload was requested but could not be created
        self.session.headers["Content-type"] = "application/octet-stream"
        self.session.headers["X-Goog-Upload-Protocol"] = "raw"
        for obj in photo_objs:
            try:
                photo_file_name = obj["filepath"]
                photo_file = open(photo_file_name, mode='rb')
                photo_bytes = photo_file.read()
            except OSError as err:
                raise RuntimeError("Could not read file \'{0}\' -- {1}".format(photo_file_name, err))
            basename = os.path.basename(photo_file_name)
            obj["basename"] = basename
            self.session.headers["X-Goog-Upload-File-Name"] = basename
            upload_token = self.session.post('https://photoslibrary.googleapis.com/v1/uploads', photo_bytes)
            if (upload_token.status_code == 200) and (upload_token.content):
                obj["token"] = upload_token.content.decode()

        create_body = {
            "albumId": self.album_id,
            "newMediaItems": [
                {
                    "description": obj["desc"],
                    "simpleMediaItem":
                        {
                            "fileName": obj["basename"],
                            "uploadToken": obj["token"]
                        }
                }
                for obj in photo_objs
            ]
        }
        resp = self.servicePH.mediaItems().batchCreate(body=create_body).execute()
        print("Server response: {}".format(resp))
        if "newMediaItemResults" in resp:
            for result in resp["newMediaItemResults"]:
                status = result["status"]
                if status.get("code") and (status.get("code") > 0):
                    raise RuntimeError(
                        "Could not add \'{0}\' to album -- {1}".format(result["filename"], status["message"]))
                else:
                    mediaItem = result["mediaItem"]
                    for obj in photo_objs:
                        if obj["filepath"].endswith(mediaItem["filename"]):
                            obj["id"] = mediaItem["id"]
        else:
            raise RuntimeError("Could not add photos to library. Server Response -- {0}".format(resp))


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


def testPhoto(app):
    gph = GPhoto()
    # gph.getAlbumsViaService()
    photo_file_list = ["images/108-0890_IMG.jpg", "images/108-0892_IMG.jpg"]
    photo_objs = [{"filepath": path, "desc": path[7:15]} for path in photo_file_list]
    print(photo_objs)
    gph.upload_photos(photo_objs)
    print(photo_objs)
    """
    [
        {'filepath': 'images/108-0890_IMG.jpg', 
         'desc': '108-0890', 
         'basename': '108-0890_IMG.jpg', 
         'token': 'CAISiQMAqD4uLWdpTAHokgTX+1BkucQXw609wn0xAfie0xnSHpRXnMyt2vGPaRczUQQmEfd9ElToE39sFcmdB5PcLbzvK5iAbYPZDlxOCaPTFa22uI7dzyGDmchyp1916eCDsdfQ/j8HUJdhDSIau5tkxITsGQGmEi4mVmW7K1nGScOewbU6N2ZBeo7grMf7u7+VYY/Znpz5MIdy+YwPvg1IaRzpNqHD1NNdyRXJHy2v091OBmmaudoB0o7Df32msEwTtfYcd/+7D/RG39zGZ5r1q1KmIt8Glg+pWLhUpRx/+Ou9LvHbs0SFwuCYowGZQEg5nZbd9mcLmLBDvKbWPQSAGyMB1fVyIdX6d3XcqF4sZgoD6HgXqOnv+EQjVPgDYeVs9nQtqNtSZjqivMfX3spKvAFLfWL3CvGJnxLcAvg4DYa1/tReCZ6PuIqlDOHjFeumtFL92v5f+qJ7Btlal5eK0XdBBXEZ4sbBt96/+jIlx3Ng42FC6MAQ8GrCA6Ub5QZat++16XPAUsu4K28', 
         'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ'
         }, 
        {'filepath': 'images/108-0892_IMG.jpg', 
         'desc': '108-0892', 
         'basename': '108-0892_IMG.jpg', 
         'token': 'CAISiQMAqD4uLZaWBq2jf/7foIArE59kBAs5DAVHrDBLD+CC5gRoXELc+so+Lz286YzzY84sj2Q6GuaoBoyGn6UeVHtj0i33kUiLojhqkaInQgFFADVBFIn+h1klBHRpDwlLQffRnUx4giuFpQ4LnDD1fldBU/UvKJ5E64SXsAnG92nGS72DFnw26uN7L9zpAOOdI9YAgzTh9QQOX/K17YGuMgFYyvbmSxpuHYGmqyoCkg30VMmpobc+F8m6Lxw+MkIGTWc20J71x7UBXZRRfhqLXQR7kWf1mXa4ndNLNyzJcybAWYU3afbV8LQLGIos1oIhpx+sD0ETfWn9P6K1MfHwAWfsktRyroqOCOQtC1xTOJB0SzUSVXKdO90wwsU1B+PuIeYr+iJPja6MLE9DIYttkKhEw/xK53rC4sIeazDU60q0CG1s28qdVgV94q/syuTUhE5qcedf33WOebYqDERLmh3kQtFvsth4auSnoY72rVs8a+NfkdYe/wmWNRisqwb7Pk9S0l3DHP7JxiU', 
         'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q'
         }
    ]
    """



if __name__ == "__main__":
    app = App()
    testPhoto(app)
"""

Server response: {
'id': 'ACKY64tFCkeXqIYLtDLAhL4ghmW0M25y-pAucOXFDQfgajRVldpKXPrFmrtFRNhekEjMB4zciQK9', 
'title': 'abstellanlagen', 
'productUrl': 
'https://photos.google.com/lr/album/ACKY64tFCkeXqIYLtDLAhL4ghmW0M25y-pAucOXFDQfgajRVldpKXPrFmrtFRNhekEjMB4zciQK9', 
'isWriteable': True}


Server response: {
    'newMediaItemResults': 
    [
        {
            'uploadToken': 'CAISiQMAqD4uLRon7FUnOOsFhBdkCCUpdbmgWnZ65XvhWtptKxmljaAMqExjUgN3MpAkVf1C82LJvv1ieDGYXKvbC9RKj0am26g2diUQ4vmRkGehoe5juaYP2B5BdfbAf74fdWTh1VG1qnowLIji/91vG00uMADrc+5A/9uY2MBTMSs2I5h18L/ohhol4uUaaVm/4FrXX8WqzZ6gX4jM+219/cF8UoYzVapcE/k5x1sDy+xLFtKmYBe7FUyAuV0/pPSgtkN+GIH8E30PAjv2wjTlied/+mqeUxpLa5pc3HdQezkhrh/dp5oMGl9twP+nLbCbNN8r2lUju5SgeMDRY90aQNxe518d85A0+qtGjMkkx4YZz6l8nCmy47mLkJfmlDyDT53GHj5lQ0Yg909PPhL7oaoz3jvEZVKXbIS4tFJMG/4FYxxenK7ZNXIjpzbWw7Vz2fSIIzgdIWBgwezPIxS73hyyy7WCyOOqzkNjqVKUfFw3eAxfRk1ooJJyS0oHhZBs6BJSsQUX21irC24',
            'status': {'message': 'Success'}, 
            'mediaItem': {
                'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ', 
                'productUrl': 'https://photos.google.com/lr/album/ACKY64tFCkeXqIYLtDLAhL4ghmW0M25y-pAucOXFDQfgajRVldpKXPrFmrtFRNhekEjMB4zciQK9/photo/ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ', 
                'mimeType': 'image/jpeg', 
                'mediaMetadata': {
                    'creationTime': '2002-12-29T12:19:35Z', 
                    'width': '1600', 
                    'height': '1200'
                }, 
                'filename': '108-0890_IMG.jpg'
            }
        }, 
        {
            'uploadToken': 'CAISiQMAqD4uLZW8VIYZ5crFmJOAz5U/sxno2f+2bSiADpYjV1ohbEot6qY5o+xMIkGO/Q2NTXbdlY+9SXCMmk0/s+G1khCKGtD66VSH//q44zdYiFT1FcT86j4uC1kZto3zEDfA5tavxzAX8d323VPhRRMuGACMroU643/i77Tk+osaGfIq9aoGkCBDv7FTa+IMACXdlWzbzIrNSgq6A2ToDjXvIXb9g3LgIt6v9WuAgg7VZ5ZbbmyhfvKG4q87sz0t+lsZjqXATKgIMRPXnjEk3lkEVFJF2H1VVOpUiu3CFqK2Gb7bSCqcWbm9esxwgIghHkGMpn9kr60DpK8Ds3PETQLTIrvjfyTWEUacnNdb9VMs1I9zoIaAiCorm66WaM1O2g1C5gaJRJdjWQWp4b989/fjo9H1r9qAMH2uCVnU1fl3MRPChVt0ndz2x2cq/HCUKsWcjL9UdiTHTV8jKPxFAUT8avHVc62MMorbclVyYhA4d0CuK9Nn7QmmjYkgbpmPUrqhDMxp9AKLpKw',
             'status': {'message': 'Success'}, 
             'mediaItem': {
                'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q', 
                'productUrl': 'https://photos.google.com/lr/album/ACKY64tFCkeXqIYLtDLAhL4ghmW0M25y-pAucOXFDQfgajRVldpKXPrFmrtFRNhekEjMB4zciQK9/photo/ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q', 
                'mimeType': 'image/jpeg', 
                'mediaMetadata': {
                    'creationTime': '2002-12-29T12:28:13Z', 
                    'width': '1600', 
                    'height': '1200'
                }, 
                'filename': '108-0892_IMG.jpg'
             }
        }
    ]
}

"""
