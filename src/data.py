import os

from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.textfield import MDTextField

import utils

class TextField(MDTextField):
    def data_event(self, *args):
        print("data1_event", args)

Builder.load_string(
"""
<TextField>:
    on_focus: if not self.focus: self.data_event()
    canvas.after:
        Color:
            rgba: 0, 1, 0, .3
        Rectangle:
            pos: self.pos
            size: self.size
    
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
            #spacing: 20
            MDTextField:
                id: typ
                name: "anlagentyp2"
                hint_text: "Anlagentyp2"
                helper_text: "Vorderradhalter, Anlehnparker"
                helper_text_mode: "on_focus"
                padding: '12dp'
                on_focus: if not self.focus: data.data_event(self)
            # TextField:
            #     id: anzahl
            #     name: "anzahl"
            #     hint_text: "Anzahl der Ständer"
            #     helper_text: "Zahl"
            #     helper_text_mode: "on_focus"
            #     padding: '12dp'
            #     on_focus: if not self.focus: data.data_event(self)
            # TextField:
            #     id: zustand
            #     name: "zustand"
            #     hint_text: "Zustand"
            #     helper_text: "gut/beschädigt/unbrauchbar"
            #     helper_text_mode: "on_focus"
            #     padding: '12dp'
            #     on_focus: if not self.focus: data.data_event(self)
            # TextField:
            #     id: bemerkung
            #     name: "bemerkung"
            #     hint_text: "Bemerkung"
            #     helper_text: "sonstiges"
            #     helper_text_mode: "on_focus"
            #     padding: '12dp'
            #     on_focus: if not self.focus: data.data_event(self)
            Image:
                id: image
                source: data.image_list[0]
                on_touch_down: app.show_images(self)
                canvas:
                    Color:
                        rgba: 1, 0, 0, .3
                    Rectangle:
                        pos: self.pos
                        size: self.size
"""
)

class Data(Screen):
    image_list = ListProperty()

    def init(self):
        pass
        # TextField:
        #     id: typ
        #     name: "anlagentyp"
        #     hint_text: "Anlagentyp"
        #     helper_text: "Vorderradhalter, Anlehnparker"
        #     helper_text_mode: "on_focus"
        #     padding: '12dp'
        #     on_focus: if not self.focus: data.data_event(self)
        # for fieldJS in self.fieldsJS:
        #     # tf = TextField(id=fieldJS.get("name"), name=fieldJS.get("name"), hint_text=fieldJS.get("hint_text"),
        #     #                helper_text=fieldJS.get("helper_text"), helper_text_mode="on_focus", padding="12dp", on_focus=self.onfocus)
        #     tf = TextField(hint_text=fieldJS.get("hint_text"), helper_text=fieldJS.get("helper_text"), text=fieldJS.get("hint_text"),
        #                    helper_text_mode="on_focus", padding="12dp")
        #     self.ids.bl.add_widget(tf, index=1)
        # self.ids.bl.do_layout()
        # self.ids.bl.canvas.ask_update()
        # 'add_widget', 'apply_class_lang_rules', 'apply_property', 'bind', 'canvas', 'center', 'center_x', 'center_y', 'children', 'clear',
        # 'clear_widgets', 'cls', 'collide_point', 'collide_widget', 'create_property', 'data_event', 'dec_disabled', 'disabled', 'dispatch',
        # 'dispatch_children', 'dispatch_generic', 'do_layout', 'events', 'export_as_image', 'export_to_png', 'fbind', 'fieldsJS', 'funbind',
        # 'get_center_x', 'get_center_y', 'get_disabled', 'get_parent_window', 'get_property_observers', 'get_right', 'get_root_window', 'get_top',
        # 'get_window_matrix', 'getter', 'height', 'id', 'ids', 'image_list', 'inc_disabled', 'init', 'is_event_type', 'layout_hint_with_bounds',
        # 'manager', 'name', 'on_enter', 'on_kv_post', 'on_leave', 'on_opacity', 'on_pre_enter', 'on_pre_leave', 'on_touch_down', 'on_touch_move',
        # 'on_touch_up', 'onfocus', 'opacity', 'parent', 'pos', 'pos_hint', 'properties', 'property', 'proxy_ref', 'register_event_type',
        # 'remove_widget', 'right', 'set_center_x', 'set_center_y', 'set_disabled', 'set_right', 'set_top', 'setter', 'size', 'size_hint',
        # 'size_hint_max', 'size_hint_max_x', 'size_hint_max_y', 'size_hint_min', 'size_hint_min_x', 'size_hint_min_y', 'size_hint_x', '
        # size_hint_y', 'to_local', 'to_parent', 'to_widget', 'to_window', 'top', 'transition_progress', 'transition_state', 'uid', 'unbind',
        # 'unbind_uid', 'unregister_event_types', 'walk', 'walk_reverse', 'width', 'x', 'y']
        # self.do_layout()


    def __init__(self, **kwargs):
        self.fieldsJS = kwargs.get("baseJS").get("felder")
        del kwargs["baseJS"]

        #images = db.getimages(lat, lon)
        impath = utils.getDataDir() + "/images"
        #imgs = sorted(os.listdir(impath))
        #self.image_list = [impath + "/" + p for p in imgs]
        #self.image_list = self.image_list[0:2]
        # self.image_list = self.image_list[0:1]
        self.image_list = []
        self.image_list.append(impath + utils.photo_image_path)
        super().__init__(**kwargs)

    def onfocus(self):
        pass

    def data_event(self, *args):
        print("data2_event", args)

    def clear(self, *args):
        print("Data clear called")
