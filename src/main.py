import locale
import os
import os.path

import plyer
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.image import AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField

import db
import kamera
import utils
from data import Data
from kamera import Kamera

Builder.load_string(
    """
#:import MapSource kivy_garden.mapview.MapSource
#:import MDDropdownMenu kivymd.uix.menu.MDDropdownMenu

<Toolbar@BoxLayout>:
    size_hint_y: None
    height: '30dp'
    padding: '4dp'
    spacing: '4dp'
    canvas:
        Color:
            rgba: .2, .2, .2, .2
        Rectangle:
            pos: self.pos
            size: self.size

<ShadedLabel@MDLabel>:
    size: self.texture_size
    canvas.before:
        Color:
            rgba: .2, .2, .2, .6
        Rectangle:
            pos: self.pos
            size: self.size

<Data>:
    id: data
    image_list: self.image_list
    on_kv_post: self.init()
    ScrollView:
        BoxLayout:
            size_hint_y: None
            height: dp(800)
            orientation: 'vertical'
            #spacing: 20
            TextField:
                id: typ
                name: "anlagentyp"
                hint_text: "Anlagentyp"
                helper_text: "Vorderradhalter, Anlehnparker"
                helper_text_mode: "on_focus"
                padding: '12dp'
                on_focus: if not self.focus: data.data_event(self)
            TextField:
                id: anzahl
                name: "anzahl"
                hint_text: "Anzahl der Ständer"
                helper_text: "Zahl"
                helper_text_mode: "on_focus"
                padding: '12dp'
                on_focus: if not self.focus: data.data_event(self)
            TextField:
                id: zustand
                name: "zustand"
                hint_text: "Zustand"
                helper_text: "gut/beschädigt/unbrauchbar"
                helper_text_mode: "on_focus"
                padding: '12dp'
                on_focus: if not self.focus: data.data_event(self)
            TextField:
                id: bemerkung
                name: "bemerkung"
                hint_text: "Bemerkung"
                helper_text: "sonstiges"
                helper_text_mode: "on_focus"
                padding: '12dp'
                on_focus: if not self.focus: data.data_event(self)
            Image:
                id: image
                source: data.image_list[0]
                on_touch_down: app.show_images(self)
                # canvas:
                #     Color:
                #         rgba: 1, 0, 0, .3
                #     Rectangle:
                #         pos: self.pos
                #         size: self.size



<Karte>:
    mv: mapview
    
    RelativeLayout:
        MapView:
            id: mapview
            lat: 48.13724404
            lon: 11.57617109
            zoom: 15
            snap_to_zoom: 1
            
            canvas:
                Color: 
                    rgba:1,0,0,0.5
                Line:
                    width:1
                    points: [self.width/2,0, self.width/2,self.height]
                Line:
                    width:1
                    points: [0, self.height/2, self.width, self.height/2]
    
            #size_hint: 0.5, 0.5
            #pos_hint: {"x": .25, "y": .25}
    
            #on_map_relocated: mapview.sync_to(self)
            #on_map_relocated: mapview.sync_to(self)
    
            # MapMarker:
            #     lat: 50.6394
            #     lon: 3.057
            # 
            # MapMarker
            #     lat: -33.867
            #     lon: 151.206
            MapMarker: # Fischbrunnen
                #size: 40,40
                lat: 48.13724404
                lon: 11.57617109
    
            MapMarker: # HBF
                #size: 20,20
                lat: 48.14025519
                lon: 11.55963407
    
        Toolbar:
            MDLabel:
                text: "Longitude: {}".format(mapview.lon)
            MDLabel:
                text: "Latitude: {}".format(mapview.lat)


<Kamera>:
    FloatLayout:
        MDLabel:
            id: path_label
            text: 'Working Directory: '
            pos_hint: {'x': 0.25, 'y': 0.8}
            size_hint: 0.5, 0.1
            
        MDTextField:
            id: filename_text
            text: 'enter_file_name_here.jpg'
            pos_hint: {'x': 0.25, 'y': .6}
            size_hint: 0.5, 0.1
            multiline: False
        
        MDRaisedButton:
            text: 'Take picture from camera!'
            pos_hint: {'x': 0.25, 'y': .3}
            size_hint: 0.5, 0.2
            on_press: root.do_capture()

<MsgPopup>:
    size_hint: .7, .4
    title: "Attention"
    
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 20

        Label:
            id: message_label
            size_hint_y: 0.4
            text: "Label"
        Button:
            text: 'Dismiss'
            size_hint_y: 0.4
            on_press: root.dismiss()
            
<Images>:
    id: images
    bl: bl
    sv: sv
    on_kv_post: self.init()

    ScrollView:
        id: sv
        BoxLayout:
            size_hint: None, None
            width: self.minimum_width
            height: self.minimum_height
            id:bl
            spacing: 10
            #canvas:
                # Color:
                #     rgba: 1, 0, 0, .3
                # Rectangle:
                #     pos: self.pos
                #     size: self.size

<MDMenuItem>:
    on_release: app.change_variable(self.text)

<Page>:
    sm: sm
    toolbar: toolbar
    BoxLayout:
        size: self.parent.size
        orientation: "vertical"
        MDToolbar:
            id: toolbar
            title: "Abstellanlagen"
            md_bg_color: app.theme_cls.primary_color
            background_palette: 'Primary'
            elevation: 10
            left_action_items: [['account', app.show_menu]]
            right_action_items: [['camera', app.show_camera],['delete', app.clear],['dots-vertical', app.show_menu2]]
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.1
            MDRaisedButton:
                text: "Zentrieren"
                size_hint: 1/4,1
                on_release: app.center(48.13724404, 11.57617109)
            MDRaisedButton:
                text: "Karte"
                size_hint: 1/4,1
                on_release: sm.current = "Karte"
            MDRaisedButton:
                text: "Daten"
                size_hint: 1/4,1
                on_release: sm.current = "Data"
            MDRaisedButton:
                text: "GPS fix"
                size_hint: 1/4,1
                on_release: app.gps_fix(self)
        ScreenManager:
            pos: self.pos
            size_hint_y: 0.9
            id: sm
            Karte: 
                name: "Karte"
   """
)


class Page(Widget):
    sm = ObjectProperty(None)


class Karte(Screen):
    pass


class Images(Screen):
    def init(self):
        pass

    def show_images(self):
        x = app
        y = app.root.sm.get_screen("Data")

        # image_list must always contain photo_image_path, otherwise image_list[0] in <Images> fails
        copy_list = [im for im in app.data.image_list if not im.endswith(utils.photo_image_path)]
        l = len(copy_list)
        if l == 0:
            app.show_camera()
            return
        elif l == 1:
            self.show_single_image(copy_list[0])
            return
        for i, cp in enumerate(copy_list):
            im = AsyncImage(source=cp, on_touch_down=self.show_single_image)
            im.size = app.root.sm.size
            im.number = i
            # without auto_bring_to_front=False the boxlayout children are reshuffled
            sc = Scatter(do_rotation=False, do_translation=False, do_scale=False, size=im.size,
                         auto_bring_to_front=False, size_hint=(None, None))
            sc.add_widget(im)
            self.bl.add_widget(sc)

    def show_single_image(self, *args):
        src = args[0].source if isinstance(args[0], AsyncImage) else args[0]
        im = AsyncImage(source=src)
        im.size = app.root.sm.size
        sc = Scatter(do_rotation=False, size=im.size, size_hint=(None, None))
        sc.add_widget(im)
        self.bl.clear_widgets()
        self.bl.add_widget(sc)


class TextField(MDTextField):
    pass


class Abstellanlagen(MDApp):
    def build(self):
        print("1build", os.name)
        if platform == 'android':
            print("2build", os.name)
            print("3build", os.name)
            perms = ["android.permission.READ_EXTERNAL_STORAGE",
                     "android.permission.WRITE_EXTERNAL_STORAGE",
                     "android.permission.CAMERA",
                     "android.permission.ACCESS_FINE_LOCATION"]
            haveperms = utils.acquire_permissions(perms)
            print("4build", os.name)
            self.gps = plyer.gps
            self.gps.configure(self.gps_onlocation, self.gps_onstatus)
            import my_camera
            self.camera = my_camera.MyAndroidCamera()

        print("6build", os.name)

        menu_labels = [
            {"viewclass": "MDMenuItem",
             "text": "Label1"},
            {"viewclass": "MDMenuItem",
             "text": "Label2"},
        ]

        dataDir = utils.getDataDir()
        os.makedirs(dataDir + "/images", exist_ok=True)
        db.initDB()
        self.root = Page()
        self.data = Data(name="Data")
        self.images = Images(name="Images")
        self.root.sm.add_widget(self.data)
        kamera.app = app
        self.root.sm.add_widget(Kamera(name="Kamera"))
        self.root.sm.add_widget(self.images)
        self.mapview = self.root.sm.current_screen.ids.mapview
        self.mapview.map_source = "osm-de"
        self.mapview.map_source.min_zoom = 11
        self.mapview.map_source.bounds = (11.4, 48.0, 11.8, 48.25)
        utils.walk("/data/user/0/de.adfcmuenchen.abstellanlagen")

        self.mddropdownmenu = MDDropdownMenu(caller=self.root.toolbar, items=menu_labels, width_mult=3)

        return self.root

    def show_menu(self, *args):
        pass

    def senden(self, *args):
        pass

    def clear(self, *args):
        cur_screen = app.root.sm.current_screen
        if cur_screen.name == "Karte":
            return
        if cur_screen.name == "Data":
            app.data.clear()
            return
        if cur_screen.name == "Images":
            if len(cur_screen.bl.children) == 0:
                return
            if len(cur_screen.bl.children) > 1:
                popup = utils.MsgPopup(
                    "Bitte ein Bild auswählen")
                popup.open()
                return
            sc = cur_screen.bl.children[0]  # Screen/BoxLayout/Scatter
            src = sc.children[0].source  # Scatter/AsyncImage
            cur_screen.bl.remove_widget(sc)
            self.data.image_list.remove(src)
            if platform == "android":
                os.remove(src)
            self.root.sm.current = "Data"

    def center(self, lat, lon):
        self.mapview.center_on(lat, lon)

    def gps_onlocation(self, **kwargs):
        lat = kwargs["lat"]
        lon = kwargs["lon"]
        self.mapview.center_on(float(lat), float(lon))
        self.gps.stop()

    def gps_onstatus(self, **kwargs):
        print("onsta", kwargs)

    def gps_fix(self, btn):
        # cannot get a continuous update to work, onlocation is called not more often than every 20 seconds
        # so update GPS loc once per button press
        if platform != 'android':
            return
        self.gps.start(minTime=10, minDistance=0)

    def show_camera(self, *args):
        self.root.sm.current = "Kamera"

    def show_images(self, *args):
        self.root.sm.current = "Images"
        self.images.show_images()

    def on_pause(self):
        print("on_pause")
        return True

    def on_resume(self):
        print("on_resume")
        pass

    def xxxx(self, *args):
        pass

    def change_variable(self, value):
        print("value=", value)

    def show_menu2(self, caller):
        self.mddropdownmenu.open()


if __name__ == '__main__':
    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = Abstellanlagen()

    app.run()

# runTouchApp(root)
