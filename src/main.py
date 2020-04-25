import locale
import os
import os.path
import sqlite3
import time

import plyer
import utils
from kivy.clock import Clock

from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivy.utils import platform


Builder.load_string(
    """
#:import MapSource kivy_garden.mapview.MapSource

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
                source: "images/photo_camera-black.png"
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


<Page>:
    sm: sm
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
            right_action_items: [['camera', app.show_camera],['delete', app.clear]]
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
            

    """
)


class Page(Widget):
    sm = ObjectProperty(None)


class Karte(Screen):
    pass

class Data(Screen):
    def init(self):
        pass

    def data_event(self, *args):
        print("data_event", args)


class MsgPopup(Popup):
    def __init__(self, msg):
        super().__init__()
        self.ids.message_label.text = msg


class Kamera(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.path_label.text = utils.getDataDir()
        self.ids.filename_text.text = time.strftime("%Y%m%d_%H%M%S") + ".jpg"
        self.toggle = True

    def do_capture(self):
        if platform != "android":
            popup = MsgPopup(
                "This feature has not yet been implemented for this platform.")
            popup.open()
            print("1docaptcb")
            if self.toggle:
                app.data.ids.image.source = "c:/temp/michaelu-1.jpg"
                self.toggle = False
            else:
                app.data.ids.image.source = "c:/temp/SeniorenTraining.jpg"
                self.toggle = True
            app.root.sm.current = "Data"

            return
        filepath = utils.getDataDir() + "/" + self.ids.filename_text.text
        print("filepath1", filepath)

        try:
            app.camera.take_picture(filename=filepath,
                                on_complete=self.camera_callback)
        except NotImplementedError:
            popup = MsgPopup(
                "This feature has not yet been implemented for this platform.")
            popup.open()

    def camera_callback(self, filepath):
        if(os.path.exists(filepath)):
            # popup = MsgPopup("Picture saved!")
            # popup.open()
            print("filepath2", filepath)
            self.filepath = filepath
            Clock.schedule_once(self.change_image) # call change_image in UI thread
            return False
        else:
            popup = MsgPopup("Konnte das Bild nicht abspeichern!")
            popup.open()
            return True

    def change_image(self,*args):
            app.data.ids.image.source = self.filepath
            app.root.sm.current = "Data"



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
            haveperms = acquire_permissions(perms)
            print("4build", os.name)
            self.gps = plyer.gps
            self.gps.configure(self.gps_onlocation, self.gps_onstatus)
            import my_camera
            self.camera = my_camera.MyAndroidCamera()

        print("6build", os.name)

        dataDir = utils.getDataDir()
        os.makedirs(dataDir, exist_ok=True)
        db = dataDir + "/Abstellanlagen.db"

        print("db path", db)
        xconn = sqlite3.connect(db)
        app.conn = xconn
        global conn
        conn = xconn
        initDB(xconn)
        self.root = Page()
        self.data = Data(name="Data")
        self.root.sm.add_widget(self.data)
        self.root.sm.add_widget(Kamera(name="Kamera"))
        self.mapview = self.root.sm.current_screen.ids.mapview
        self.mapview.map_source = "osm-de"
        self.mapview.map_source.min_zoom = 11
        self.mapview.map_source.bounds = (11.4, 48.0, 11.8, 48.25)
        walk("/data/user/0/de.adfcmuenchen.abstellanlagen")
        return self.root

    def show_menu(self, *args):
        pass

    def senden(self, *args):
        pass

    def clear(self, *args):
        pass

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
        print("show_images1", args)
        print("show_images2", args[0])
        print("show_images3", args[0].source) #/storage/emulated/0/Android/data/de.adfc-muenchen.abstellanlagen/files/20200425_182442.jpg
        if args[0].source == "images/photo_camera-black.png":
            self.show_camera()
            return
        print("show_images4")
        pass

    def on_pause(self):
        print("on_pause")
        return True

    def on_resume(self):
        print("on_resume")
        pass


def walk(p):
    print("walk", p)
    try:
        if os.path.isdir(p):
            for cp in sorted(os.listdir(p)):
                walk(p + "/" + cp)
    except Exception as e:
        print("walk", p, ":", e)


def initDB(conn):
    # c = conn.cursor()
    # try:
    #     with conn:
    #         c.execute("""CREATE TABLE arbeitsblatt(
    #         tag TEXT,
    #         fnr INTEGER,
    #         einsatzstelle TEXT,
    #         beginn TEXT,
    #         ende TEXT,
    #         fahrtzeit TEXT,
    #         mvv_euro TEXT,
    #         kh INTEGER)
    #         """)
    # except OperationalError:
    #     pass
    # try:
    #     with conn:
    #         c.execute("""CREATE TABLE eigenschaften(
    #         vorname TEXT,
    #         nachname TEXT,
    #         wochenstunden TEXT,
    #         emailadresse TEXT)
    #         """)
    # except OperationalError:
    #     pass
    # try:
    #     with conn:
    #         c.execute("""delete from arbeitsblatt where einsatzstelle="" and beginn="" and ende="" """)
    # except OperationalError:
    pass


def acquire_permissions(permissions, timeout=30):
    from plyer.platforms.android import activity

    def allgranted(permissions):
        print("permallg1", permissions)
        for perm in permissions:
            print("permallg2", perm)
            r = activity.checkCurrentPermission(perm)
            print("permallg3", perm, r)
            if r == 0:
                return False
        print("permallg4")
        return True

    print("1perm", permissions)
    haveperms = allgranted(permissions)
    print("2perm", haveperms)
    if haveperms:
        # we have the permission and are ready
        return True

    # invoke the permissions dialog
    activity.requestPermissions(permissions)
    print("3perm")

    # now poll for the permission (UGLY but we cant use android Activity's onRequestPermissionsResult)
    t0 = time.time()
    while time.time() - t0 < timeout and not haveperms:
        print("4perm")
        # in the poll loop we could add a short sleep for performance issues?
        haveperms = allgranted(permissions)
        time.sleep(1)

    print("5perm", haveperms)
    return haveperms


if __name__ == '__main__':
    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = Abstellanlagen()

    app.run()

# runTouchApp(root)
