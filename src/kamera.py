import os
import time

from kivy import platform
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

import utils

global app

class Kamera(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.path_label.text = utils.getDataDir() + "/images"
        self.ids.filename_text.text = time.strftime("%Y%m%d_%H%M%S") + ".jpg"
        self.toggle = True

    def do_capture(self):
        if platform != "android":
            popup = utils.MsgPopup(
                "This feature has not yet been implemented for this platform.")
            popup.open()
            print("1docaptcb")
            if self.toggle:
                app.data.image_list.insert(0, "c:/temp/michaelu-1.jpg")
                self.toggle = False
            else:
                app.data.image_list.insert(0, "c:/temp/SeniorenTraining.jpg")
                self.toggle = True
            app.root.sm.current = "Data"
            return

        filepath = utils.getDataDir() + "/images" + self.ids.filename_text.text
        try:
            app.camera.take_picture(filename=filepath, on_complete=self.camera_callback)
        except NotImplementedError:
            popup = utils.MsgPopup(
                "This feature has not yet been implemented for this platform.")
            popup.open()

    def camera_callback(self, filepath):
        if (os.path.exists(filepath)):
            # popup = MsgPopup("Picture saved!")
            # popup.open()
            self.filepath = filepath
            Clock.schedule_once(self.change_image)  # call change_image in UI thread
            return False
        else:
            popup = utils.MsgPopup("Konnte das Bild nicht abspeichern!")
            popup.open()
            return True

    def change_image(self, *args):
        app.data.image_list.insert(0, self.filepath)
        app.root.sm.current = "Data"


