import os
import time

from kivy import platform
from kivy.clock import Clock
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog

import utils

global app

class Kamera:
    def __init__(self, app, **kwargs):
        self.app = app
        super().__init__(**kwargs)
        self.toggle = True

    def do_capture(self):
        if platform != "android":
            self.app.dialog = MDDialog(size_hint=(.8, .4), title="OS-Spezifisch", text="Kamera ist nur auf Android verfügbar",
                                   buttons=[
                                       MDFlatButton(
                                           text="Weiter", text_color=self.app.theme_cls.primary_color,
                                           on_press=self.app.dismiss_dialog
                                       )])
            self.app.dialog.open()
            print("1docaptcb")
            if self.toggle:
                filename = "108-0890_IMG.jpg"
                self.toggle = False
            else:
                filename = "108-0892_IMG.jpg"
                self.toggle = True

            self.filepath = utils.getDataDir() + "/images/" + filename
            if not os.path.exists(self.filepath):
                raise Exception("???")
            self.app.data.addImage(filename, self.filepath)
            self.app.root.sm.current = "Data"
            return

        self.filename = time.strftime("%Y%m%d_%H%M%S") + ".jpg"
        self.filepath = utils.getDataDir() + "/images/" + self.filename
        try:
            self.app.camera.take_picture(filename=self.filepath, on_complete=self.camera_callback)
        except NotImplementedError:
            # popup = utils.MsgPopup(
            #     "This feature has not yet been implemented for this platform.")
            # popup.open()
            self.app.dialog = MDDialog(size_hint=(.8, .4), title="OS-Spezifisch", text="Kamera ist nur auf Android verfügbar",
                                   buttons=[
                                       MDFlatButton(
                                           text="Weiter", text_color=self.app.theme_cls.primary_color,
                                           on_press=self.app.dismiss_dialog
                                       )])
            self.app.dialog.open()

    def camera_callback(self, _):
        if (os.path.exists(self.filepath)):
            # popup = MsgPopup("Picture saved!")
            # popup.open()
            Clock.schedule_once(self.change_image)  # call change_image in UI thread
            return False
        else:
            # popup = utils.MsgPopup("Konnte das Bild nicht abspeichern!")
            # popup.open()
            self.app.dialog = MDDialog(size_hint=(.8, .4), title="Fehler", text="Konnte das Bild nicht abspeichern!",
                                   buttons=[
                                       MDFlatButton(
                                           text="Weiter", text_color=self.app.theme_cls.primary_color,
                                           on_press=self.app.dismiss_dialog
                                       )])
            self.app.dialog.open()
            return True


    def change_image(self, *args):
        self.app.data.addImage(self.filename, self.filepath)
        self.app.root.sm.current = "Data"


