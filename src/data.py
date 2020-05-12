import gc
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
            height: dp(800) + self.minimum_height
            orientation: 'vertical'
            #spacing: 10
            MDRaisedButton:
                text: "Zusatzdaten"
                size_hint: 1,0.1
                on_release: root.show_zusatz()
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

<Zusatz>:
    id: zusatz
    on_kv_post: self.init()
    ScrollView:
        BoxLayout:
            id:bl
            size_hint_y: None
            height: dp(400) + self.minimum_height
            orientation: 'vertical'
            BoxLayout:
                size: self.width,20
                MDRaisedButton:
                    text: "<"
                    size_hint: 1/3,0.2
                    on_release: root.next(-1)
                MDRaisedButton:
                    text: "+"
                    size_hint: 1/3,0.2
                    on_release: root.neu()
                MDRaisedButton:
                    text: ">"
                    size_hint: 1/3,0.2
                    on_release: root.next(1)
            Widget:
"""
)


class TextField(MDTextField):
    def __init__(self, data, name, **kwargs):
        self.feldname = name
        self.data = data
        super().__init__(**kwargs)

    def data_event(self, *args):
        self.data.update(self.feldname, self.text, self.data.app.mapview.lat, self.data.app.mapview.lon)


class Data(Screen):
    image_list = ListProperty()

    def __init__(self, app, **kwargs):
        self.app = app
        self.fieldsJS = self.app.baseJS.get("felder")
        self.fields = {}
        self.impath = utils.getDataDir() + "/images/"

        self.image_list = ["./images/" + utils.photo_image_path]
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
            self.ids.bl.add_widget(tf, index=2)

    def update(self, *args):
        self.db.update_data(*args)

    def setData(self):
        #gc.collect()
        # get images for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        imgs = list(set(self.db.get_images(self.lat, self.lon)))
        # photo_image must be the last or the only one
        imlist = [self.impath + p for p in imgs]
        imlist.append("./images/" + utils.photo_image_path)

        imlist2 = []
        for p in imlist:
            if os.path.exists(p):
                imlist2.append(p)
            else:
                print("cannot access", p)
                # raise Exception("cannot access " + p)
        self.image_list = imlist2

        # get data for lat/lon
        values = self.db.get_data(self.lat, self.lon)
        print("data values", values, self.lat, self.lon)
        if values is None:
            for name in self.fields.keys():
                field = self.fields[name]
                field.text = ""
        else:
            for name in self.fields.keys():
                field = self.fields[name]
                field.text = str(values[name])
                # db entry may have come from a nearby lat, lon
                self.lat = values["lat"]
                self.lon = values["lon"]

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

    def addImage(self, filename, filepath, lat, lon):
        self.db.insert_image(filename, lat, lon)
        self.image_list.insert(0, filepath)

    def show_zusatz(self):
        if self.app.checkAlias():
            self.app.zusatz.setZusatz(-1)
            self.app.pushScreen("Zusatz")


class Zusatz(Screen):
    def __init__(self, app, **kwargs):
        self.app = app
        self.fieldsJS = self.app.baseJS.get("zusatz")
        self.fields = {}
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

    def update(self, *args):
        if self.numbers is None or self.number is None:
            nr = None
        else:
            nr = self.numbers[self.number]
        rowid = self.db.update_zusatz(nr, *args)
        if nr is None:
            self.setZusatz(rowid)

    def setZusatz(self, nr):
        # get zusatz (additional, 1:n) data for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        self.numbers = self.db.get_zusatz_numbers(self.lat, self.lon)
        if len(self.numbers) == 0:
            for name in self.fields.keys():
                field = self.fields[name]
                field.text = ""
            self.number = None
        else:
            try:
                self.number = self.numbers.index(nr)
            except:
                self.number = 0
            self.setZusatz2()

    def setZusatz2(self):
        nr = self.numbers[self.number]
        values = self.db.get_zusatz(nr)
        print("zusatz values", values)
        for name in self.fields.keys():
            field = self.fields[name]
            field.text = str(values[name])
        self.creator = values["creator"]

    def clear(self, *args):
        if self.numbers is None or self.number is None:
            return
        nr = self.numbers[self.number]
        self.db.delete_zusatz(nr)
        self.setZusatz(-1)

    def next(self, inc):
        n = self.number + inc
        if n < 0 or n >= len(self.numbers):
            return
        self.number = n
        self.setZusatz2()

    def neu(self):
        for name in self.fields.keys():
            field = self.fields[name]
            field.text = ""
        self.number = None
