import os

from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.textfield import MDTextField

import db
import utils

Builder.load_string("""
<TextField>:
    on_focus: if not self.focus: self.daten_event()
    
<Daten>:
    id: daten
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
                id:zsbtn
                text: "Zusatzdaten"
                size_hint: 1,0.1
                on_release: root.show_zusatz()
            Image:
                id: image
                source: root.image_list[0][0]
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
                #pos: 0,0
                #size_hint: 1,0.1
                size: self.width,20
                MDFillRoundFlatIconButton:
                    icon: "arrow-left-bold-box"
                    text: "Zurück"
                    user_font_size: "64sp"
                    on_release: root.next(-1)
                    size_hint: 1/4,0.2
                MDFillRoundFlatIconButton:
                    icon: "plus-box"
                    text: "Neu"
                    user_font_size: "64sp"
                    on_release: root.neu()
                    size_hint: 1/3,0.2
                MDFillRoundFlatIconButton:
                    icon: "arrow-right-bold-box"
                    text: "Vor"
                    user_font_size: "64sp"
                    on_release: root.next(1)
                    size_hint: 1/3,0.2
            Widget:
                         
"""
                    )


def checkProtected(obj):
    if obj.protected and obj.creator != obj.dbinst.aliasname:
        obj.app.msgDialog("Nicht erlaubt", "Eintrag wurde von anderem Benutzer erzeugt")
        return True
    return False


class TextField(MDTextField):
    def __init__(self, daten, name, type, limited, **kwargs):
        self.daten = daten
        self.feldname = name
        self.feldtype = type
        self.limited = limited
        super().__init__(**kwargs)

    def yes(self):
        t = self.text.lower()
        if len(t) == 0:
            return ("", None)
        if t == "1" or t[0] == "y" or t[0] == "j":
            return ("ja", 1)
        return ("nein", 0)

    def limit(self):
        t = self.text.lower()
        if len(t) == 0:
            return ("", None)
        for l in self.limited:
            if t[0] == l[0]:
                return (l,l)
        return ("", None)

    def daten_event(self, *args):
        if self.feldtype == "bool":
            self.text, val = self.yes()
        elif self.limited is not None:
            self.text, val = self.limit()
        else:
            val = self.text if self.text != "" else None
        self.daten.update(self.feldname, val, self.daten.app.mapview.lat, self.daten.app.mapview.lon)


class Form(Screen):
    def init(self):
        std = [("created", "Erzeugt"), ("modified", "Geändert")]
        for t in std:
            tf = TextField(self, t[0], "string", None)
            tf.hint_text = t[1]
            tf.helper_text = ""
            tf.text = ""
            tf.padding = "12dp"
            tf.disabled = True
            self.fields[t[0]] = tf
            self.ids.bl.add_widget(tf, index=2)
        for fieldJS in self.fieldsJS:
            # tf=TextField(hint_text="xxx", ..) does not work!?
            name = fieldJS.get("name")
            type = fieldJS.get("type")
            limited = fieldJS.get("limited", None)
            tf = TextField(self, name, type, limited)
            tf.hint_text = fieldJS.get("hint_text")
            tf.helper_text = fieldJS.get("helper_text")
            tf.text = ""
            tf.helper_text_mode = "on_focus"
            tf.padding = "12dp"
            self.fields[name] = tf
            self.ids.bl.add_widget(tf, index=2)

    def setValues(self, values):
        if values is None:
            for name in self.fields.keys():
                field = self.fields[name]
                field.text = ""
                self.creator = self.dbinst.aliasname
        else:
            for name in self.fields.keys():
                field = self.fields[name]
                v = values[name]
                if v is None:
                    v = ""
                elif field.feldtype == "bool":
                    v = "ja" if v else "nein"
                elif field.feldtype == "prozent":
                    v = str(v) + "%"
                field.text = str(v)
            self.creator = values["creator"]


class Daten(Form):
    image_list = ListProperty()

    def __init__(self, app, **kwargs):
        self.app = app
        self.fieldsJS = self.app.baseJS.get("daten").get("felder")
        self.protected = self.app.baseJS.get("protected", False)
        self.fields = {}

        self.image_list = [(utils.getCurDir() + "/images/" + utils.camera_icon, None)]
        self.dbinst = db.DB.instance()
        super().__init__(**kwargs)
        if self.app.baseJS.get("zusatz", None) is None:
            self.ids.zsbtn.disabled = True


    def setDaten(self):
        # gc.collect()
        # get images for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        img_tuples = self.dbinst.get_images(self.lat, self.lon)
        imlist = []
        for tuple in img_tuples:  # (image_path, None)  or (mediaId, image_url)
            if tuple[1]:
                if hasattr(self.app, "gphoto"):
                    img = self.app.gphoto.getImage(tuple[0], 200)
                else:
                    img = self.app.serverIntf.getImage(tuple[0], 200)
                if img is not None:
                    imlist.append((img, tuple[0]))
            else:
                imlist.append((utils.getDataDir() + "/images/" + tuple[0], None))
        # photo_image must be the last or the only one
        imlist.append((utils.getCurDir() + "/images/" + utils.camera_icon, None))

        imlist2 = []
        for p in imlist:
            if os.path.exists(p[0]):
                imlist2.append(p)
            else:
                print("cannot access", p[0])
                # raise Exception("cannot access " + p)
        self.image_list = imlist2

        # get daten for lat/lon
        values = self.dbinst.get_daten(self.lat, self.lon)
        print("daten values", values, self.lat, self.lon)
        self.setValues(values)
        if values is not None:
            self.lat = values["lat"]
            self.lon = values["lon"]

    def update(self, *args):
        if checkProtected(self):
            return
        self.dbinst.update_daten(*args)

    def clear(self, *args):
        if checkProtected(self):
            return
        self.dbinst.delete_daten(self.lat, self.lon)
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
        self.dbinst.insert_image(filename, lat, lon)
        self.image_list.insert(0, (filepath, None))

    def show_zusatz(self):
        if self.app.checkAlias():
            self.app.zusatz.setZusatz(-1)
            self.app.pushScreen("Zusatz")


class Zusatz(Form):
    def __init__(self, app, **kwargs):
        self.app = app
        zusatz = self.app.baseJS.get("zusatz", None)
        self.fieldsJS = [] if zusatz is None else zusatz.get("felder", [])
        self.protected = self.app.baseJS.get("protected", False)
        self.fields = {}
        self.dbinst = db.DB.instance()
        super().__init__(**kwargs)

    def update(self, *args):
        if checkProtected(self):
            return
        if self.numbers is None or self.number is None:
            nr = None
        else:
            nr = self.numbers[self.number]
        rowid = self.dbinst.update_zusatz(nr, *args)
        if nr is None:
            self.setZusatz(rowid)

    def setZusatz(self, nr):
        # get zusatz (additional, 1:n) daten for lat/lon
        mv = self.app.mapview
        self.lat, self.lon = mv.lat, mv.lon
        self.numbers = self.dbinst.get_zusatz_numbers(self.lat, self.lon)
        if len(self.numbers) == 0:
            self.setValues(None)
            self.number = None
            self.creator = self.dbinst.aliasname
        else:
            try:
                self.number = self.numbers.index(nr)
            except:
                self.number = 0
            self.setZusatz2()

    def setZusatz2(self):
        nr = self.numbers[self.number]
        values = self.dbinst.get_zusatz(nr)
        print("zusatz values", values)
        self.setValues(values)

    def clear(self, *args):
        if self.numbers is None or self.number is None:
            return
        if checkProtected(self):
            return
        nr = self.numbers[self.number]
        self.dbinst.delete_zusatz(nr)
        self.setZusatz(-1)

    def next(self, inc):
        if self.number is None:
            return
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
        self.creator = self.dbinst.aliasname
