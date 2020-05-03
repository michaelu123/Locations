import locale
import os
import os.path

import plyer
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy_garden.mapview import MapMarker
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem

import config
import db
import utils
from data import Data
from kamera import Kamera

Builder.load_string(
    """
#:import MapSource kivy_garden.mapview.MapSource

<Account>:
    on_kv_post: self.init()
    id: account
    GridLayout:
        cols: 1
        spacing: 20
        padding: 30
        MDTextField:
            id: vorname
            name: "vorname"
            hint_text: "Vorname"
            on_focus: if not self.focus: account.accountEvent()
        MDTextField:
            id: nachname
            name: "nachname"
            hint_text: "Nachname"
            on_focus: if not self.focus: account.accountEvent()
        MDTextField:
            id: aliasname
            name: "aliasname"
            hint_text: "Aliasname"
            helper_text: "Alias- oder Spitzname"
            helper_text_mode: "on_focus"
            on_focus: if not self.focus: account.accountEvent()
        MDTextField:
            id: emailadresse
            name: "emailadresse"
            hint_text: "Email-Adresse"
            on_focus: if not self.focus: account.accountEvent()

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

<Karte>:
    mv: mapview
    
    RelativeLayout:
        MapView:
            id: mapview
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
        Toolbar:
            MDLabel:
                text: "Longitude: {}".format(mapview.lon)
            MDLabel:
                text: "Latitude: {}".format(mapview.lat)

<MyMapMarker>:
    on_press: app.clickMarker(self)

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
            margin: 10,10
            canvas.before:
                Color:
                    rgba: 1, 0, 0, .2
                Rectangle:
                    pos: self.pos
                    size: self.size

<Single>:
    id: single
    im: im

    ScrollView:
        id: sv
        Scatter:
            size_hint: None, None
            do_rotation: False
            size: app.root.sm.size
            AsyncImage:
                id: im
                size: app.root.sm.size
                canvas.before:
                    Color:
                        rgba: 0, 1, 0, .2
                    Rectangle:
                        pos: self.pos
                        size: self.size



<MDMenuItem>:
    on_release: app.change_variable(self.text)
    
<ItemConfirm>
    on_release: app.set_icon(check, self)
    CheckboxRightWidget:
        id: check
        group: "check"
        on_release: app.set_icon(check, root) # call set_icon for click on checkbox and label


<Page>:
    sm: sm
    datenbtn: datenbtn
    toolbar: toolbar
    BoxLayout:
        size: self.parent.size
        orientation: "vertical"
        MDToolbar:
            id: toolbar
            title: "Locations"
            md_bg_color: app.theme_cls.primary_color
            background_palette: 'Primary'
            elevation: 10
            left_action_items: [['account', app.show_account]]
            right_action_items: [['camera', app.do_capture],['delete', app.clear],['dots-vertical', app.show_menu]]
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.1
            MDRaisedButton:
                text: "Zentrieren"
                size_hint: 1/4,1
                on_release: app.center()
            MDRaisedButton:
                text: "Karte"
                size_hint: 1/4,1
                on_release: sm.current = "Karte"
            MDRaisedButton:
                id: datenbtn
                text: "Eigenschaften" if sm.current == "Account" else "Daten"
                size_hint: 1/4,1
                on_release: app.show_data()
            MDRaisedButton:
                text: "GPS fix"
                size_hint: 1/4,1
                on_release: app.gps_fix(self)
        ScreenManager:
            pos: self.pos
            size_hint_y: 0.9
            id: sm
   """
)

class Account(Screen):
    def accountEvent(self):
        app.store.put("account",
                      vorname = self.ids.vorname.text,
                      nachname = self.ids.nachname.text,
                      aliasname=self.ids.aliasname.text,
                      emailadresse=self.ids.emailadresse.text)

    def init(self):
        try:
            acc = app.store.get("account")
        except:
            acc = {"vorname":"", "nachname":"", "aliasname":"", "emailadresse":""}
        self.ids.vorname.text = acc["vorname"]
        self.ids.nachname.text = acc["nachname"]
        self.ids.aliasname.text = acc["aliasname"]
        self.ids.emailadresse.text = acc["emailadresse"]


class MyMapMarker(MapMarker):
    pass


class Page(Widget):
    sm = ObjectProperty(None)


class Karte(Screen):
    pass


class Single(Screen):
    pass


class Images(Screen):
    def init(self):
        pass

    def show_images(self):
        # image_list must always contain photo_image_path, otherwise image_list[0] in <Images> fails
        copy_list = [im for im in app.data.image_list if not im.endswith(utils.photo_image_path)]
        l = len(copy_list)
        if l == 0:
            app.do_capture()
            return
        elif l == 1:
            self.show_single_image(copy_list[0])
            return
        self.bl.clear_widgets()
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
        app.single.ids.im.source = src
        app.root.sm.current = "Single"


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Locations(MDApp):
    def build(self):
        if platform == 'android':
            perms = ["android.permission.READ_EXTERNAL_STORAGE",
                     "android.permission.WRITE_EXTERNAL_STORAGE",
                     "android.permission.CAMERA",
                     "android.permission.ACCESS_FINE_LOCATION"]
            haveperms = utils.acquire_permissions(perms)
            self.gps = plyer.gps
            self.gps.configure(self.gps_onlocation, self.gps_onstatus)
            import my_camera
            self.camera = my_camera.MyAndroidCamera()

        dataDir = utils.getDataDir()
        os.makedirs(dataDir + "/images", exist_ok=True)

        try:
            self.config = config.Config(self)
        except Exception as e:
            s = utils.printExToString("Konfigurationsfehler", e)
            print(s)
            self.error = s
            Clock.schedule_once(self.show_error, 2)
            return
        self.config = config.Config(self)
        self.store = JsonStore("base.json")
        self.root = Page()
        try:
            base = self.store.get("base")["base"]
        except:
            base = self.config.getNames()[0]
        self.setup(base)

        # utils.walk("/data/user/0/de.adfcmuenchen.abstellanlagen")
        return self.root

    def setup(self, base):
        self.selected_base = base
        self.root.toolbar.title = self.selected_base
        self.root.datenbtn.text = self.selected_base

        self.store.put("base", base=self.selected_base)
        self.baseJS = self.config.getBase(self.selected_base)
        self.dbinst = db.DB.instance()
        self.dbinst.initDB(self)

        # self.root.sm.clear_widgets() does not work !?
        sm_screens = self.root.sm.screens[:]
        self.root.sm.clear_widgets(sm_screens)
        sm_screens = None

        self.karte = Karte(name="Karte")
        self.root.sm.add_widget(self.karte)

        self.mapview = self.karte.ids.mapview
        self.mapview.map_source = "osm-de"
        self.mapview.map_source.min_zoom = self.config.getMinZoom(self.selected_base)
        self.mapview.map_source.bounds = self.config.getGPSArea(self.selected_base)

        self.images = Images(name="Images")
        self.root.sm.add_widget(self.images)

        self.single = Single(name="Single")
        self.root.sm.add_widget(self.single)

        self.data = Data(self, name="Data")
        self.root.sm.add_widget(self.data)

        self.kamera = Kamera(self)
        self.account = Account(name="Account")
        self.root.sm.add_widget(self.account)

        markers = self.dbinst.getMarkerLocs()
        for marker in markers:
            self.mapview.add_marker(MyMapMarker(lat=marker[0], lon=marker[1]))
        self.center()
        self.root.sm.current = "Karte"

    def show_account(self, *args):
        self.root.sm.current = "Account"

    def senden(self, *args):
        pass

    def clear(self, *args):
        cur_screen = self.root.sm.current_screen
        if cur_screen.name == "Karte":
            return
        if cur_screen.name == "Data":
            self.data.clear()
            return
        if cur_screen.name == "Images":
            self.msgDialog("Auswahl", "Bitte ein Bild auswählen")
            return
        if cur_screen.name == "Single":
            src = cur_screen.im.source
            if platform == "android":
                os.remove(src)
            src = os.path.basename(src)
            self.dbinst.delete_images(self.mapview.lat, self.mapview.lon, src)
            self.show_data()

    def msgDialog(self, titel, text):
        self.dialog = MDDialog(size_hint=(.8, .4), title=titel, text=text,
           buttons=[
               MDFlatButton(
                   text="Weiter", text_color=self.theme_cls.primary_color,
                   on_press=self.dismiss_dialog
               )])
        self.dialog.open()

    def dismiss_dialog(self, *args):
        self.dialog.dismiss()

    def center(self):
        gps = self.baseJS.get("gps")
        lat = gps.get("center_lat")
        lon = gps.get("center_lon")
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

    def show_images(self, *args):
        self.root.sm.current = "Images"
        self.images.show_images()

    def show_data(self):
        print("1show_data")
        self.data.setData()
        self.mapview.center_on(self.data.lat, self.data.lon)
        self.root.sm.current = "Data"
        self.checkAlias()
        print("2show_data")

    def on_pause(self):
        print("on_pause")
        return True

    def on_resume(self):
        print("on_resume1")
        base = self.store.get("base")["base"]
        self.setup(base)
        pass

    def change_base(self, *args):
        self.dismiss_dialog()
        items = self.items
        for item in items:
            if item.ids.check.active:
                t = item.text
                if t != self.selected_base:
                    self.setup(t)
                    return

    def change_variable(self, value):
        print("value=", value)

    def show_menu(self, *args):
        basen = list(self.config.getNames())
        items = [ItemConfirm(text=base) for base in basen]
        x = basen.index(self.selected_base)
        for i, item in enumerate(items):
            items[i].ids.check.active = i == x
        self.items = items
        buttons = [MDFlatButton(text="OK", text_color=self.theme_cls.primary_color, on_press=app.change_base)]
        self.dialog = MDDialog(size_hint=(.8, .4), type="confirmation", title="Auswahl der Datenbasis",
                               text="Bitte Datenbasis auswählen",
                               items=items, buttons=buttons)
        self.dialog.open()

    def set_icon(self, instance_check, x):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False

    def add_marker(self, lat, lon):
        self.mapview.add_marker(MyMapMarker(lat=lat, lon=lon))

    def clickMarker(self, marker):
        self.mapview.center_on(marker.lat, marker.lon)
        self.show_data()

    def do_capture(self, *args):
        if self.checkAlias():
            self.kamera.do_capture(self.mapview.lat, self.mapview.lon)

    def checkAlias(self):
        if not self.account.ids.aliasname.text:
            self.dialog = MDDialog(size_hint=(.8, .4), title="Account", text="Bitte den Aliasnamen ausfüllen",
                                   buttons=[
                                       MDFlatButton(
                                           text="Weiter", text_color=self.theme_cls.primary_color,
                                           on_press=self.dismiss_dialog
                                       )])
            self.dialog.open()
            self.root.sm.current = "Account"
            return False
        return True

    def show_error(self, *args):
        self.msgDialog("Konfigurationsfehler", self.error)




if __name__ == '__main__':
    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = Locations()

    app.run()
