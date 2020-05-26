import os
import shutil
import time

from kivy import platform
from kivy.clock import Clock, mainthread
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

import utils

class Kamera:
    def __init__(self, app, **kwargs):
        self.app = app
        self.stellen = app.baseJS.get("gps").get("nachkommastellen")
        super().__init__(**kwargs)
        self.toggle = True

    def do_capture(self, lat, lon):
        self.lat = lat
        self.lon = lon
        lat_round = str(round(lat, self.stellen))
        lon_round = str(round(lon, self.stellen))
        self.filename = lat_round + "_" + lon_round + "_" + time.strftime("%Y%m%d_%H%M%S") + ".jpg"
        self.filepath = utils.getDataDir() + "/images/" + self.filename

        if platform != "android":
            self.app.msgDialog("OS-Spezifisch", "Kamera ist nur auf Android verfügbar")
            if self.toggle:
                filename = "108-0890_IMG.jpg"
                self.toggle = False
            else:
                filename = "108-0892_IMG.jpg"
                self.toggle = True
            shutil.copyfile("./images/" + filename, self.filepath)
            self.app.daten.addImage(self.filename, self.filepath, lat, lon)
            #self.app.root.sm.current = "Daten"
            self.app.on_pause()
            self.app.on_resume()
            return

        try:
            self.app.camera.take_picture(filename=self.filepath, on_complete=self.camera_callback)
        except NotImplementedError:
            self.app.msgDialog("OS-Spezifisch", "Kamera ist nur auf Android verfügbar")

    def camera_callback(self, _):
        if (os.path.exists(self.filepath)):
            self.change_image()
            return False
        else:
            self.app.msgDialog("Fehler", "Konnte das Bild nicht abspeichern!")
            return True


    @mainthread
    def change_image(self, *args):
        self.app.daten.addImage(self.filename, self.filepath, self.lat, self.lon)
        self.app.show_daten(False)


