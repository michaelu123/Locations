import os

from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivymd.uix.textfield import MDTextField

import utils

#class TextField(TextInput):
class TextField(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def data_event(self, *args):
        print("data1_event", self, args, self.text, self.name)

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
                source: data.image_list[0]
                on_touch_down: root.img_touch_down(args)
"""
)

class Data(Screen):
    image_list = ListProperty()

    def init(self):
        for fieldJS in self.fieldsJS:
            # tf=TextField(hint_text="xxx", ..) does not work!?
            tf = TextField()
            tf.hint_text=fieldJS.get("hint_text")
            tf.helper_text=fieldJS.get("helper_text")
            tf.text=""
            tf.helper_text_mode="on_focus"
            tf.padding="12dp"
            tf.name = fieldJS.get("name")
            self.ids.bl.add_widget(tf, index=1)


    def __init__(self, app, baseJS, **kwargs):
        self.fieldsJS = baseJS.get("felder")
        self.app = app

        #images = db.getimages(lat, lon)
        impath = utils.getDataDir() + "/images"
        imgs = sorted(os.listdir(impath))
        self.image_list = [impath + "/" + p for p in imgs]

        self.image_list = self.image_list[0:2]
        # self.image_list = self.image_list[0:1]
        #self.image_list = []
        self.image_list.append(impath + utils.photo_image_path)
        super().__init__(**kwargs)

    def clear(self, *args):
        print("Data clear called")

    def img_touch_down(self, args):
        # cannot understand why I have to check for mouse pos here?
        # if I do not check, show_images is called on the whole boxlayout!?
        # args[0] is always the Image, args1 the MouseMotionEvent
        if args[0].collide_point(args[1].pos[0], args[1].pos[1]):
            self.app.show_images(self, args)
