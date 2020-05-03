import os

from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.textfield import MDTextField

import db
import utils

Builder.load_string("""
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
        self.data.db.update_data(self.feldname, self.text, self.data.lat, self.data.lon)


class Data(Screen):
    image_list = ListProperty()

    def __init__(self, app, **kwargs):
        self.app = app
        self.fieldsJS = self.app.baseJS.get("felder")
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
            tf.hint_text = fieldJS.get("hint_text")
            tf.helper_text = fieldJS.get("helper_text")
            tf.text = ""
            tf.helper_text_mode = "on_focus"
            tf.padding = "12dp"
            self.fields[name] = tf
            self.ids.bl.add_widget(tf, index=1)

    def setData(self):
        print("1setData")
        # get images for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        imgs = list(set(self.db.get_images(self.lat, self.lon)))
        # photo_image must be the last or the only one
        imgs.append(utils.photo_image_path)
        imlist = [self.impath + p for p in imgs]
        print("image_list", imlist)

        imlist2 = []
        for p in imlist:
            if os.path.exists(p):
                imlist2.append(p)
            else:
                print("cannot access", p)
                # raise Exception("cannot access " + p)
        self.image_list = imlist2
        print("2setData", imlist2)

        # get data for lat/lon
        values = self.db.get_data(self.lat, self.lon)
        for name in self.fields.keys():
            field = self.fields[name]
            field.text = str(values[name]) if values is not None else ""
        print("3setData")

    def clear(self, *args):
        self.db.delete_data(self.lat, self.lon)
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
        mv = self.app.mapview
        self.db.insert_image(filename, mv.lat, mv.lon)
        self.image_list.insert(0, filepath)
