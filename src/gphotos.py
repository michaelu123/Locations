import os

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build

import config
import utils
from gsheets import Google


# https://developers.google.com/photos/library/reference/rest/v1/mediaItems
# https://developers.google.com/photos/library/guides/access-media-items
# https://stackoverflow.com/questions/50573196/access-google-photo-api-with-python-using-google-api-python-client

class GPhoto(Google):
    def __init__(self, app):
        self.app = app
        self.baseJS = app.baseJS
        self.getServicePH()
        self.album_name = self.baseJS.get("db_tabellenname")  # use also as album name
        self.getSharedAlbum()

    # get service more often than necessary for fear of expiring credentials
    def getServicePH(self):
        creds = self.getCreds()
        self.servicePH = build('photoslibrary', 'v1', credentials=creds)

    def getSharedAlbum(self):
        # Call the Photo v1 API
        results = self.servicePH.sharedAlbums().list(
            excludeNonAppCreatedData=True, pageSize=10).execute()  # , fields="nextPageToken,sharedalbums(id,title)"
        items = results.get('sharedAlbums', [])
        for a in items:
            if a["title"] == self.album_name:
                self.album_id = a["id"]
                return
        self.joinSharedAlbum()

    # for shared albums: https://developers.google.com/photos/library/guides/share-media
    # NOTE: shared album MUST be created with this code, using the creds of the app
    # It must not be created via GPhotos UI!
    def createSharedAlbum(self):
        create_album_body = {"album": {"title": self.album_name}}
        resp = self.servicePH.albums().create(body=create_album_body).execute()
        print(resp)
        # {
        #     'id': 'ACKY64u2oPLRfQInuxAI_WCx_bF2C589MQPuVc2jxBcaCI9zm2Oqrl9Nq3kba8Nz_s_iyDMvtZR8',
        #     'title': 'abstellanlagen',
        #     'productUrl': 'https://photos.google.com/lr/album/<id>',
        #     'isWriteable': True
        # }

        if "id" in resp:
            self.album_id = resp['id']
        else:
            raise RuntimeError(
                "Could not create shared photo album '{0}'. Server Response: {1}".format(self.album_name, resp))
        share_album_body = {"sharedAlbumOptions": {"isCollaborative": "true", "isCommentable": "true"}}
        resp = self.servicePH.albums().share(albumId=self.album_id, body=share_album_body).execute()
        print("sharealbum", resp)
        self.baseJS["shareToken"] = resp["shareInfo"]["shareToken"]
        print("shareToken", self.baseJS["shareToken"])
        # {
        #     'shareInfo':
        #     {
        #         'sharedAlbumOptions': {'isCollaborative': True, 'isCommentable': True},
        #         'shareableUrl': 'https://photos.app.goo.gl/Ff9uGg21Q7LiqNSZ6',
        #         'shareToken': 'AOVP0rQZIEqQOiIUX3O86yxslicTgrKTPZqJI38QuPJkss9_FWn2MrXN4DnB0Ne1B36BPWG3uL6uaABf0dTd2ns0PrgTy_xolYIe0OFCJdxZPg4FPWXiwEifK1eHXekQd0I',
        #         'isJoined': True,
        #         'isOwned': True
        #     }
        # }

    def joinSharedAlbum(self):
        shareToken = self.baseJS.get("shareToken")
        if not shareToken:
            raise ValueError("shareToken nicht konfiguriert")
        if shareToken == "TODO":
            self.album_id = None
            return
        join_shared_album_body = {"shareToken": self.baseJS.get("shareToken")}
        resp = self.servicePH.sharedAlbums().join(body=join_shared_album_body).execute()
        self.album_id = resp["album"]["id"]
        print("joinshared", resp)
        # {
        #     'album':
        #     {
        #         'id': 'ABBrZPQRbS4PB7NlMEuc_1JnvC7rfus65W957OgXIi1bZLx4MQRv6HD-2n4cLVfED-7sGp51rXs8eoSOaYV-nxWvBRysUPrXBA',
        #         'title': 'abstellanlagen',
        #         'productUrl': 'https://photos.google.com/lr/album/ABBrZPQRbS4PB7NlMEuc_1JnvC7rfus65W957OgXIi1bZLx4MQRv6HD-2n4cLVfED-7sGp51rXs8eoSOaYV-nxWvBRysUPrXBA',
        #         'isWriteable': True,
        #         'shareInfo':
        #         {
        #             'sharedAlbumOptions': {'isCollaborative': True, 'isCommentable': True},
        #             'shareableUrl': 'https://photos.app.goo.gl/Ff9uGg21Q7LiqNSZ6',
        #             'shareToken': 'AOVP0rQZIEqQOiIUX3O86yxslicTgrKTPZqJI38QuPJkss9_FWn2MrXN4DnB0Ne1B36BPWG3uL6uaABf0dTd2ns0PrgTy_xolYIe0OFCJdxZPg4FPWXiwEifK1eHXekQd0I'
        #         }
        #     }
        # }

    # from https://github.com/eshmu/gphotos-upload
    # or https://learndataanalysis.org/upload-media-items-google-photos-api-and-python-part-4/
    # photo_objs = { "filepath": path, "desc": description }
    # we add "token": uploadtoken, "id": mediaItemId
    # Achtung: Es gibt ein Limit von 20000 Photos pro Album!
    # Resumable uploads described in https://developers.google.com/photos/library/guides/resumable-uploads
    # but this uploads only one image at a time
    def upload_photos(self, photo_objs):
        for obj in photo_objs:
            try:
                photo_file_path = obj["filepath"]
                with open(photo_file_path, mode='rb') as photo_file:
                    photo_bytes = photo_file.read()
            except OSError as err:
                raise RuntimeError("Could not read file '{0}' -- {1}".format(photo_file_path, err))
            basename = os.path.basename(photo_file_path)
            obj["basename"] = basename
            self.session = AuthorizedSession(self.getCreds())
            self.session.headers["Content-type"] = "application/octet-stream"
            self.session.headers["X-Goog-Upload-Content-Type"] = "image/jpeg"
            self.session.headers["X-Goog-Upload-Protocol"] = "raw"
            self.session.headers["X-Goog-Upload-File-Name"] = basename
            upload_token = self.session.post('https://photoslibrary.googleapis.com/v1/uploads', photo_bytes, timeout=999999)
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
        self.getServicePH()
        resp = self.servicePH.mediaItems().batchCreate(body=create_body).execute()
        # print("batchCreate response: {}".format(resp))
        # {
        #     'newMediaItemResults':
        #         [
        #             {
        #                 'uploadToken': '...',
        #                 'status': {'message': 'Success'},
        #                 'mediaItem': {
        #                     'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
        #                     'productUrl': 'https://photos.google.com/lr/album/<album id>/photo/<id>',
        #                     'mimeType': 'image/jpeg',
        #                     'mediaMetadata': {
        #                         'creationTime': '2002-12-29T12:19:35Z',
        #                         'width': '1600',
        #                         'height': '1200'
        #                     },
        #                     'filename': '108-0890_IMG.jpg'
        #                 }
        #             },
        #             {
        #                 'uploadToken': '...',
        #                 'status': {'message': 'Success'},
        #                 'mediaItem': {
        #                     'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q',
        #                     'productUrl': 'https://photos.google.com/lr/album/<album id>/photo/<id>',
        #                     'mimeType': 'image/jpeg',
        #                     'mediaMetadata': {
        #                         'creationTime': '2002-12-29T12:28:13Z',
        #                         'width': '1600',
        #                         'height': '1200'
        #                     },
        #                     'filename': '108-0892_IMG.jpg'
        #                 }
        #             }
        #         ]
        # }

        if "newMediaItemResults" in resp:
            for result in resp["newMediaItemResults"]:
                status = result["status"]
                if status.get("code") and (status.get("code") > 0):
                    raise RuntimeError(
                        "Could not add '{0}' to album -- {1}".format(result["filename"], status["message"]))
                mediaItem = result["mediaItem"]
                for obj in photo_objs:
                    if obj["token"] == result["uploadToken"]:
                        obj["id"] = mediaItem["id"]
                        obj["url"] = mediaItem["productUrl"]
                        break
        else:
            raise RuntimeError("Could not add photos to library. Server Response -- {0}".format(resp))

    def getImage(self, id, w=0, h=0):
        self.getServicePH()
        item = self.servicePH.mediaItems().get(mediaItemId=id).execute()
        # print("get", item)
        # {
        #     'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
        #     'description': '108-0890',
        #     'productUrl': 'https://photos.google.com/lr/photo/<id>',
        #     'baseUrl': 'https://lh3.googleusercontent.com/lr/...',
        #     'mimeType': 'image/jpeg',
        #     'mediaMetadata':
        #     {
        #         'creationTime': '2002-12-29T12:19:35Z',
        #         'width': '1600',
        #         'height': '1200',
        #         'photo': {
        #             'cameraMake': 'Canon',
        #             'cameraModel': 'Canon PowerShot A40',
        #             'focalLength': 5.40625,
        #             'apertureFNumber': 2.8,
        #             'isoEquivalent': 161
        #         }
        #     },
        #     'filename': '108-0890_IMG.jpg'
        # }

        baseUrl = item["baseUrl"]
        filename = item["filename"]
        if not w:
            w = item["mediaMetadata"]["width"]
        if not h:
            h = item["mediaMetadata"]["height"]
        filename = utils.getDataDir() + f"/images/{w}x{h}_{filename}"
        if os.path.exists(filename):
            return filename

        self.session = AuthorizedSession(self.getCreds())
        resp = self.session.get(baseUrl + f"=w{w}-h{h}")
        try:
            with open(filename, mode='wb') as photo_file:
                photo_bytes = photo_file.write(resp.content)
                return filename
        except OSError as err:
            raise RuntimeError("Could not write file '{0}' -- {1}".format(filename, err))

    def batchGetImages(self, ids, w=0, h=0):
        self.getServicePH()
        resp = self.servicePH.mediaItems().batchGet(mediaItemIds=ids).execute()
        # print("batchGet", resp)
        # {
        #     'mediaItemResults':
        #     [
        #         {
        #             'mediaItem':
        #             {
        #                 'id': 'ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ',
        #                 'description': '108-0890',
        #                 'productUrl': 'https://photos.google.com/lr/photo/<id>',
        #                 'baseUrl': 'https://lh3.googleusercontent.com/lr/...',
        #                 'mimeType': 'image/jpeg',
        #                 'mediaMetadata':
        #                 {
        #                     'creationTime': '2002-12-29T12:19:35Z',
        #                     'width': '1600',
        #                     'height': '1200',
        #                     'photo':
        #                     {
        #                         'cameraMake': 'Canon',
        #                         'cameraModel': 'Canon PowerShot A40',
        #                         'focalLength': 5.40625,
        #                         'apertureFNumber': 2.8,
        #                         'isoEquivalent': 161
        #                     }
        #                 },
        #                 'filename': '108-0890_IMG.jpg'
        #             }
        #         },
        #         {
        #             'mediaItem':
        #             {
        #                 'id': 'ACKY64tCnuPHj3n6FotGexaADmysKTVdqT19klegKel5P853FGrfxNQ9vFKsfwwT4uRcgrPL0tT7nY8Mj7yf8DHgffCQW_tK8Q',
        #                 'description': '108-0892',
        #                 'productUrl': 'https://photos.google.com/lr/photo/<id>',
        #                 'baseUrl': 'https://lh3.googleusercontent.com/lr/...',
        #                 'mimeType': 'image/jpeg',
        #                 'mediaMetadata':
        #                 {
        #                     'creationTime': '2002-12-29T12:28:13Z',
        #                     'width': '1600',
        #                     'height': '1200',
        #                     'photo':
        #                     {
        #                         'cameraMake': 'Canon',
        #                         'cameraModel': 'Canon PowerShot A40',
        #                         'focalLength': 5.40625,
        #                         'apertureFNumber': 2.8,
        #                         'isoEquivalent': 50
        #                     }
        #                 },
        #                 'filename': '108-0892_IMG.jpg'
        #             }
        #         }
        #     ]
        # }

        items = resp["mediaItemResults"]
        for item in items:
            baseUrl = item["mediaItem"]["baseUrl"]
            filename = item["mediaItem"]["filename"]
            if w == 0:
                w = item["mediaItem"]["mediaMetadata"]["width"]
            if h == 0:
                h = item["mediaItem"]["mediaMetadata"]["height"]
            self.session = AuthorizedSession(self.getCreds())
            resp = self.session.get(baseUrl + f"=w{w}-h{h}")
            try:
                with open(utils.getDataDir() + f"/images/{w}x{h}_" + filename, mode='wb') as photo_file:
                    photo_bytes = photo_file.write(resp.content)
            except OSError as err:
                raise RuntimeError("Could not write file '{0}' -- {1}".format(filename, err))


def getShareToken(app):
    # start with a shareToken in config file with value "TODO"
    gph = GPhoto(app)
    userinfo = gph.get_user_info(gph.getCreds())
    print("userinfo", userinfo)
    if gph.album_id is None:
        gph.createSharedAlbum()


def test(app):
    gph = GPhoto(app)
    userinfo = gph.get_user_info(gph.getCreds())
    print("userinfo", userinfo)
    photo_file_list = ["images/108-0890_IMG.jpg", "images/108-0892_IMG.jpg"]
    photo_objs = [{"filepath": path, "desc": path[7:15]} for path in photo_file_list]
    # print(photo_objs)
    gph.upload_photos(photo_objs)
    # print(photo_objs)

    # gph.album_name = "xxxshared"
    # gph.create_or_retrieve_album()

    mediaIds = ['ACKY64ut147fmVuJ9rn_L38vK_-Xyf2m9fhbHShoXnTjtDrH1eBCR24hIhxYlkLF-65dMr4onkmIal6tqEmCTFs-nDBiJKFTgQ']
    # gph.batchGetImages(mediaIds, 200, 200)
    # gph.batchGetImages(mediaIds, 0, 0)
    for id in mediaIds:
        gph.getImage(id, 100, 100)


class App:
    def __init__(self, arg):
        cfg = config.Config()
        self.baseJS = cfg.getBase(arg)


if __name__ == "__main__":
    app = App("Sitzbänke")
    getShareToken(app)
