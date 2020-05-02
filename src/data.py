import os

from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivymd.uix.textfield import MDTextField

import db
import utils

Builder.load_string(
"""
<TextField>:
    on_focus: if not self.focus: self.data_event()
    
<Data>:
    id: data
    image_list: self.image_list
    on_kv_post: self.init()
    ScrollView:
        BoxLayout:
            id:bl
            size_hint_y: None
            height: dp(800)
            orientation: 'vertical'
            #spacing: 10
            Image:
                id: image
                source: root.image_list[0]
                on_touch_down: root.img_touch_down(args)
                canvas:
                    Color:
                        rgba: 0, 0, 0, .2
                    Rectangle:
                        pos: self.pos
                        size: self.size
"""
)

class TextField(MDTextField):
    def __init__(self, data, name, **kwargs):
        self.feldname = name
        self.data = data
        super().__init__(**kwargs)

    def data_event(self, *args):
        self.db.update_data(self.feldname, self.text, self.data.lat, self.data.lon)


class Data(Screen):
    image_list = ListProperty()

    def __init__(self, app, baseJS, **kwargs):
        self.fieldsJS = baseJS.get("felder")
        self.app = app
        self.fields = {}
        self.impath = utils.getDataDir() + "/images/"
        self.image_list = [self.impath + utils.photo_image_path]
        self.db = db.DB.instance()
        super().__init__(**kwargs)

    def init(self):
        for fieldJS in self.fieldsJS:
            # tf=TextField(hint_text="xxx", ..) does not work!?
            name = fieldJS.get("name")
            tf = TextField(self, name)
            tf.hint_text=fieldJS.get("hint_text")
            tf.helper_text=fieldJS.get("helper_text")
            tf.text=""
            tf.helper_text_mode="on_focus"
            tf.padding="12dp"
            self.fields[name] = tf
            self.ids.bl.add_widget(tf, index=1)

    def setData(self):
        # get images for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        imgs = self.db.getimages(self.lat, self.lon)
        imgs.append(utils.photo_image_path)
        self.image_list = [self.impath + p for p in sorted(imgs)]

        if not os.path.exists(self.image_list[0]):
            raise Exception("???")

        # get data for lat/lon
        values = self.db.getdata(self.lat, self.lon)
        for name in self.fields.keys():
            field = self.fields[name]
            field.text = str(values[name]) if values is not None else ""

    def clear(self, *args):
        for name in self.fields.keys():
            field = self.fields[name]
            field.text = ""

    def img_touch_down(self, args):
        # cannot understand why I have to check for mouse pos here?
        # if I do not check, show_images is called on the whole boxlayout!?
        # args[0] is always the Image, args1 the MouseMotionEvent
        if args[0].collide_point(args[1].pos[0], args[1].pos[1]):
            self.app.show_images(self, args)

    def addImage(self, filename, filepath):
        self.db.insert_image(filename, self.lat, self.lon)
        self.image_list.insert(0, filepath)

