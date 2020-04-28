import os

from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
import utils


class Data(Screen):
    image_list = ListProperty()

    def __init__(self, *args, **kwargs):
        impath = utils.getDataDir() + "/images"
        imgs = sorted(os.listdir(impath))
        self.image_list = [impath + "/" + p for p in imgs]
        self.image_list = self.image_list[0:2]
        # self.image_list = self.image_list[0:1]
        # self.image_list = []
        self.image_list.append(impath + utils.photo_image_path)
        super().__init__(**kwargs)

    def init(self):
        pass

    def data_event(self, *args):
        print("data_event", args)

    def clear(self, *args):
        print("Data clear called")
