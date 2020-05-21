import os

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build

import config
from gsheets import Google


# https://developers.google.com/photos/library/reference/rest/v1/mediaItems
# https://developers.google.com/photos/library/guides/access-media-items
# https://stackoverflow.com/questions/50573196/access-google-photo-api-with-python-using-google-api-python-client


class GPhoto(Google):
    def __init__(self, app):
        self.app = app
        self.baseJS = app.baseJS
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
        self.album_id = self.baseJS.get("album_id")
        # self.album_id = self.create_or_retrieve_album()

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
        """
        {
            'id': 'ACKY64tFCkeXqIYLtDLAhL4ghmW0M25y-pAucOXFDQfgajRVldpKXPrFmrtFRNhekEjMB4zciQK9', 
            'title': 'abstellanlagen', 
            'productUrl': 'https://photos.google.com/lr/album/<id>', 
            'isWriteable': True
        }
        """
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
    # Resumable uploads described in https://developers.google.com/photos/library/guides/resumable-uploads
    # but this uploads only one image at a time
    def upload_photos(self, photo_objs):
        self.session = AuthorizedSession(self.getCreds())
        self.session.headers["Content-type"] = "application/octet-stream"
        self.session.headers["X-Goog-Upload-Content-Type"] = "image/jpeg"
        self.session.headers["X-Goog-Upload-Protocol"] = "raw"
        for obj in photo_objs:
            try:
                photo_file_name = obj["filepath"]
                with open(photo_file_name, mode='rb') as photo_file:
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
        """
        print("batchCreate response: {}".format(resp))
        {
            'newMediaItemResults':
                [
                    {
                        'uploadToken': '...',
                        'status': {'message': 'Success'},
                        'mediaItem': {
                            'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
                            'productUrl': 'https://photos.google.com/lr/album/<album id>/photo/<id>',
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
                        'uploadToken': '...',
                        'status': {'message': 'Success'},
                        'mediaItem': {
                            'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q',
                            'productUrl': 'https://photos.google.com/lr/album/<album id>/photo/<id>',
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

    def getImage(self, id, w=0, h=0):
        item = self.servicePH.mediaItems().get(mediaItemId=id).execute()
        """
        print("get", item)
        {
            'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
            'description': '108-0890',
            'productUrl': 'https://photos.google.com/lr/photo/<id>',
            'baseUrl': 'https://lh3.googleusercontent.com/lr/...',
            'mimeType': 'image/jpeg',
            'mediaMetadata': 
            {
                'creationTime': '2002-12-29T12:19:35Z', 
                'width': '1600', 
                'height': '1200',
                'photo': {
                    'cameraMake': 'Canon', 
                    'cameraModel': 'Canon PowerShot A40',
                    'focalLength': 5.40625, 
                    'apertureFNumber': 2.8, 
                    'isoEquivalent': 161
                }
            },
            'filename': '108-0890_IMG.jpg'
        }
        """
        self.session = AuthorizedSession(self.getCreds())
        baseUrl = item["baseUrl"]
        filename = item["filename"]
        if w == 0:
            w = item["mediaMetadata"]["width"]
        if h == 0:
            h = item["mediaMetadata"]["height"]
        resp = self.session.get(baseUrl + f"=w{w}-h{h}")
        print(resp)
        try:
            with open(f"{w}x{h}_" + filename, mode='wb') as photo_file:
                photo_bytes = photo_file.write(resp.content)
        except OSError as err:
            raise RuntimeError("Could not write file \'{0}\' -- {1}".format(filename, err))

    def batchGetImages(self, ids, w=0, h=0):
        resp = self.servicePH.mediaItems().batchGet(mediaItemIds=ids).execute()
        """
        print("batchGet", resp)
        {
            'mediaItemResults': 
            [
                {
                    'mediaItem': 
                    {
                        'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ', 
                        'description': '108-0890', 
                        'productUrl': 'https://photos.google.com/lr/photo/<id>', 
                        'baseUrl': 'https://lh3.googleusercontent.com/lr/...', 
                        'mimeType': 'image/jpeg', 
                        'mediaMetadata': 
                        {
                            'creationTime': '2002-12-29T12:19:35Z', 
                            'width': '1600', 
                            'height': '1200', 
                            'photo': 
                            {
                                'cameraMake': 'Canon', 
                                'cameraModel': 'Canon PowerShot A40', 
                                'focalLength': 5.40625, 
                                'apertureFNumber': 2.8, 
                                'isoEquivalent': 161
                            }
                        }, 
                        'filename': '108-0890_IMG.jpg'
                    }
                }, 
                {
                    'mediaItem': 
                    {
                        'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q', 
                        'description': '108-0892', 
                        'productUrl': 'https://photos.google.com/lr/photo/<id>', 
                        'baseUrl': 'https://lh3.googleusercontent.com/lr/...', 
                        'mimeType': 'image/jpeg', 
                        'mediaMetadata': 
                        {
                            'creationTime': '2002-12-29T12:28:13Z', 
                            'width': '1600', 
                            'height': '1200', 
                            'photo': 
                            {
                                'cameraMake': 'Canon', 
                                'cameraModel': 'Canon PowerShot A40', 
                                'focalLength': 5.40625, 
                                'apertureFNumber': 2.8, 
                                'isoEquivalent': 50
                            }
                        }, 
                        'filename': '108-0892_IMG.jpg'
                    }
                }
            ]
        }
        """
        items = resp["mediaItemResults"]
        self.session = AuthorizedSession(self.getCreds())
        for item in items:
            baseUrl = item["mediaItem"]["baseUrl"]
            filename = item["mediaItem"]["filename"]
            if w == 0:
                w = item["mediaItem"]["mediaMetadata"]["width"]
            if h == 0:
                h = item["mediaItem"]["mediaMetadata"]["height"]
            resp = self.session.get(baseUrl + f"=w{w}-h{h}")
            print(resp)
            try:
                with open(f"{w}x{h}_" + filename, mode='wb') as photo_file:
                    photo_bytes = photo_file.write(resp.content)
            except OSError as err:
                raise RuntimeError("Could not write file \'{0}\' -- {1}".format(filename, err))


def testPhoto(app):
    gph = GPhoto(app)
    # gph.getAlbumsViaService()
    # photo_file_list = ["images/108-0890_IMG.jpg", "images/108-0892_IMG.jpg"]
    # photo_objs = [{"filepath": path, "desc": path[7:15]} for path in photo_file_list]
    # print(photo_objs)
    # gph.upload_photos(photo_objs)
    # print(photo_objs)
    """
    [
        {'filepath': 'images/108-0890_IMG.jpg', 
         'desc': '108-0890', 
         'basename': '108-0890_IMG.jpg', 
         'token': '...', 
         'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ'
         }, 
        {'filepath': 'images/108-0892_IMG.jpg', 
         'desc': '108-0892', 
         'basename': '108-0892_IMG.jpg', 
         'token': '...', 
         'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q'
         }
    ]
    """
    mediaIds = ['ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
                'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q']
    gph.batchGetImages(mediaIds, 200, 200)
    gph.batchGetImages(mediaIds, 0, 0)
    for id in mediaIds:
        gph.getImage(id, 100, 100)


class App:
    def __init__(self):
        cfg = config.Config()
        self.baseJS = cfg.getBase("Abstellanlagen")


if __name__ == "__main__":
    app = App()
    testPhoto(app)
