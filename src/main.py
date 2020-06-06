import json
import locale
import os
import os.path
import time
from concurrent.futures.thread import ThreadPoolExecutor

import plyer
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import Screen
from kivy.uix.settings import SettingsWithSidebar
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy_garden.mapview import MapMarker
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.uix.spinner import MDSpinner

import bugs
import config
import db
import gphotos
import gsheets
import utils
from data import Daten, Zusatz
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
            snap_to_zoom: False
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
            on_map_relocated: app.map_relocated()
        Toolbar:
            MDLabel:
                text: "Zoom: {}".format(mapview.zoom)
            MDLabel:
                text: "Lon: {}".format(round(mapview.lon, 6))
            MDLabel:
                text: "Lat: {}".format(round(mapview.lat, 6))

<MyMapMarker>:
    on_touch_move: pass
    #on_press: app.clickMarker(self)
    on_release: app.clickMarker(self)
    
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



<ItemConfirm>
    on_release: root.set_icon(check)
    
    CheckboxRightWidget:
        id: check
        group: "check"
        #on_release: root.set_icon(check, root) # call set_icon for click on checkbox and label


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
            left_action_items: [['menu', app.open_settings], ['account', app.show_account]]
            right_action_items: [['camera', app.do_capture],['delete', app.clear],['dots-vertical', app.show_bases]]
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.1
            MDRaisedButton:
                text: "Laden"
                size_hint: 1/5,1
                on_release: app.loadSheet(True)
            MDRaisedButton:
                text: "Speichern"
                size_hint: 1/5,1
                on_release: app.storeSheet()
            MDRaisedButton:
                text: "Karte"
                size_hint: 1/5,1
                on_release: app.pushScreen("Karte")
            MDRaisedButton:
                id: datenbtn
                text: "Eigenschaften" if sm.current == "Account" else "Daten"
                size_hint: 1/5,1
                on_release: app.show_daten(False)
            MDRaisedButton:
                text: "GPS fix"
                size_hint: 1/5,1
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
                      vorname=self.ids.vorname.text,
                      nachname=self.ids.nachname.text,
                      aliasname=self.ids.aliasname.text,
                      emailadresse=self.ids.emailadresse.text)

    def init(self):
        try:
            acc = app.store.get("account")
        except:
            acc = {"vorname": "", "nachname": "", "aliasname": "", "emailadresse": ""}
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
    def __init__(self, app, **kwargs):
        self.app = app
        super().__init__(**kwargs)


class Images(Screen):
    def __init__(self, app, **kwargs):
        self.app = app
        super().__init__(**kwargs)

    def init(self):
        pass

    def show_images(self):
        # image_list must always contain camera_icon, otherwise image_list[0] in <Images> fails
        copy_list = [im for im in app.daten.image_list if not im[0].endswith(utils.camera_icon)]
        l = len(copy_list)
        if l == 0:
            app.do_capture()
            return
        elif l == 1:
            self.show_single_image(copy_list[0])
            return
        self.bl.clear_widgets()
        for i, cp in enumerate(copy_list):
            im = AsyncImage(source=cp[0], on_touch_down=self.show_single_image)
            im.size = app.root.sm.size
            im.mediaId = cp[1]
            im.number = i
            # without auto_bring_to_front=False the boxlayout children are reshuffled
            sc = Scatter(do_rotation=False, do_translation=False, do_scale=False, size=im.size,
                         auto_bring_to_front=False, size_hint=(None, None))
            sc.add_widget(im)
            self.bl.add_widget(sc)

    def show_single_image(self, *args):
        # if called for a single gphoto, show the thumbnail
        # when clicked on the thumbnail, show the full image
        if isinstance(args[0], AsyncImage):
            if args[0].mediaId is None:
                src = args[0].source
            else:
                maxdim = self.app.getConfigValue("maxdim", 1024)
                src = self.app.gphoto.getImage(args[0].mediaId, w=maxdim, h=maxdim)
        else: # tuple(path, url)
            src = args[0][0]
        app.single.ids.im.source = src
        app.root.sm.current = "Single"


class ItemConfirm(OneLineAvatarIconListItem):
    divider = None

    def set_icon(self, instance_check):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False


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

        Window.bind(on_keyboard=self.popScreen)
        os.makedirs(utils.getDataDir() + "/images", exist_ok=True)
        self.markerMap = {}
        self.settings_cls = SettingsWithSidebar
        self.curMarker = None
        self.relocated = 0
        self.dialog = None

        self.baseConfig = config.Config()
        self.error = self.baseConfig.getErrors()
        if self.error:
            Clock.schedule_once(self.show_error, 2)
        self.store = JsonStore("base.json")
        self.root = Page()
        try:
            base = self.store.get("base")["base"]
            self.baseConfig.getBase(self.base)
        except:
            base = self.baseConfig.getNames()[0]
        print("base", base)
        # print("----------- /data/user/0/de.adfcmuenchen.abstellanlagen")
        # utils.walk("/data/user/0/de.adfcmuenchen.abstellanlagen")
        # print("----------- cwd", os.getcwd())
        # utils.walk(".")
        # print("------------getDataDir", utils.getDataDir())
        # utils.walk(utils.getDataDir())
        # print("------------getExternalFilesDir", utils.getExternalFilesDir())
        # utils.walk(utils.getExternalFilesDir())
        self.executor = ThreadPoolExecutor(max_workers = 1)
        self.future = None

        laststored = self.getConfigValue("gespeichert")
        if not laststored:
            self.setConfigValue("gespeichert", time.strftime("%Y.%m.%d %H:%M:%S"))

        self.setup(base)
        return self.root

    def setup(self, base):
        self.selected_base = base
        self.root.toolbar.title = self.selected_base
        self.root.datenbtn.text = self.selected_base

        self.store.put("base", base=self.selected_base)
        self.baseJS = self.baseConfig.getBase(self.selected_base)
        self.stellen = self.baseJS.get("gps").get("nachkommastellen")

        # self.root.sm.clear_widgets() does not work !?
        sm_screens = self.root.sm.screens[:]
        self.root.sm.clear_widgets(sm_screens)
        sm_screens = None
        self.spinner = MDSpinner(size=(100, 100), size_hint=(None, None), pos_hint={"center_x": .5, "center_y": .5})

        self.karte = Karte(name="Karte")
        self.root.sm.add_widget(self.karte)

        self.mapview = self.karte.ids.mapview
        self.mapview.map_source = "osm-de"
        self.mapview.map_source.min_zoom = self.baseConfig.getMinZoom(self.selected_base)
        self.mapview.map_source.max_zoom = 19
        self.mapview.map_source.bounds = self.baseConfig.getGPSArea(self.selected_base)
        # Hack, trying to fix random zoom bug
        #self.mapview._scatter.scale_min = 0.5  # MUH was 0.2
        #self.mapview._scatter.scale_max: 2.0  # MUH was 3!?

        self.images = Images(self, name="Images")
        self.root.sm.add_widget(self.images)

        self.single = Single(self, name="Single")
        self.root.sm.add_widget(self.single)

        self.kamera = Kamera(self)
        self.account = Account(name="Account")
        self.root.sm.add_widget(self.account)

        self.daten = Daten(self, name="Daten")
        self.root.sm.add_widget(self.daten)

        self.zusatz = Zusatz(self, name="Zusatz")
        self.root.sm.add_widget(self.zusatz)

        self.pushScreen("Karte")

        if self.future is not None:
            self.future.result()
        self.future = self.executor.submit(self.setup2, base)

    def setup2(self, base):
        self.dbinst = db.DB.instance()
        self.dbinst.initDB(self)

        self.message("Mit Google Sheets verbinden")
        self.gsheet = gsheets.GSheet(self)
        userInfo = self.gsheet.get_user_info(self.gsheet.getCreds())
        self.message("Mit Google Photos verbinden als " + userInfo["name"])
        self.gphoto = gphotos.GPhoto(self)

        self.loadSheet(False)

    def show_markers(self, *args):
        self.message("Lade Map Marker")
        self.spinnerStart()
        clat = self.mapview.centerlat
        clon = self.mapview.centerlon
        minlat = clat - 0.013
        maxlat = clat + 0.013
        minlon = clon - 0.013
        maxlon = clon + 0.013

        for k in list(self.markerMap.keys()):
            # lat, lon = k.split(":")
            # lat = float(lat)
            # lon = float(lon)
            # if not (minlat < lat < maxlat and minlon < lon < maxlon):
            #     markerOld = self.markerMap.get(k)
            #     self.mapview.remove_marker(markerOld)
            #     del self.markerMap[k]
            markerOld = self.markerMap.get(k)
            self.mapview.remove_marker(markerOld)
            del self.markerMap[k]

        sheetValues = self.gsheet.getValuesWithin(minlat, maxlat, minlon, maxlon)
        self.dbinst.fillWith(sheetValues)
        markers = self.dbinst.getMarkerLocs(minlat, maxlat, minlon, maxlon)
        self.show_markers2(markers)

    @mainthread
    def show_markers2(self, markers):
        for marker in markers:
            self.add_marker(marker[0], marker[1])
        self.spinnerStop()

    def show_account(self, *args):
        self.pushScreen("Account")

    def clear(self, *args):
        cur_screen = self.root.sm.current_screen
        if cur_screen.name == "Karte":
            return
        if cur_screen.name == "Daten":
            self.daten.clear()
            lat, lon = self.centerLatLon()
            self.add_marker(round(lat, self.stellen), round(lon, self.stellen))
            return
        if cur_screen.name == "Zusatz":
            self.zusatz.clear()
            return
        if cur_screen.name == "Images":
            self.msgDialog("Auswahl", "Bitte ein Bild auswählen")
            return
        if cur_screen.name == "Single":
            src = cur_screen.im.source
            os.remove(src)
            src = os.path.basename(src)
            lat, lon = self.centerLatLon()
            self.dbinst.delete_images(lat, lon, src)
            self.add_marker(round(lat, self.stellen), round(lon, self.stellen))
            self.show_daten(False)

    @mainthread
    def msgDialog(self, titel, text):
        if self.dialog is not None:
            self.dialog_dismiss()
        self.dialog = MDDialog(size_hint=(.8, .4), title=titel, text=text,
                               buttons=[
                                   MDFlatButton(
                                       text="Weiter", text_color=self.theme_cls.primary_color,
                                       on_press=self.dialog_dismiss
                                   )])
        self.dialog.auto_dismiss = False
        self.dialog.open()

    def dialog_dismiss(self, *args):
        self.dialog.dismiss(animation=False, force=True)
        self.dialog = None

    def loadSheet(self, newCenter):
        if newCenter and self.future.running():
            return
        if newCenter:
            lat = self.mapview.lat
            lon = self.mapview.lon
            self.store.put("latlon", lat=lat, lon=lon)
        else:
            try:
                lat = self.store.get("latlon")["lat"]
                lon = self.store.get("latlon")["lon"]
            except:
                lat = lon = 0
            if lat == 0 or lon == 0:
                gps = self.baseJS.get("gps")
                lat = gps.get("center_lat")
                lon = gps.get("center_lon")
        self.center_on(lat, lon)
        if newCenter: # called from UI
            self.future = self.executor.submit(self.show_markers)
        else:
            self.show_markers()

    def storeImages(self, newImgs):
        # tuples to list, skip if image_path=row[6] is already a mediaId
        # assume a mediaId is loooong
        unsavedImgs = [list(row) for row in newImgs if len(row[6]) < 60]
        # don't store already saved images again in gphoto:
        savedImgs = [list(row) for row in newImgs if len(row[6]) > 60]
        photo_objs = [{"filepath": utils.getDataDir() + "/images/" + row[6],
                       "desc": row[6][0:row[6].index(".jpg")]} for row in unsavedImgs]
        # if len(photo_objs) > 0:
        #     self.gphoto.upload_photos(photo_objs)
        pcnt = len(photo_objs)
        for i, photo_obj in enumerate(photo_objs):
            self.message(f"Speichere Bild {i+1} von {pcnt}")
            self.gphoto.upload_photos([photo_obj])
        for i, row in enumerate(unsavedImgs):
            old_image_path = row[6]
            new_image_path = photo_objs[i]["id"]
            new_image_url = photo_objs[i]["url"]
            self.dbinst.update_imagepath(old_image_path, new_image_path, new_image_url, row[4], row[5])
            row[6] = new_image_path
            row[7] = new_image_url
        # store all of them in gsheets (duplicates removed by gsheet script)
        unsavedImgs.extend(savedImgs)
        return unsavedImgs, photo_objs

    def storeSheet(self):
        if self.checkAlias():
            if self.future.running():
                self.msgDialog("Läuft noch", "Ein früherer Speichervorgang läuft noch!")
                return
            self.spinnerStart()
            self.future = self.executor.submit(self.storeSheet2)

    def storeSheet2(self, *args):
        laststored = self.getConfigValue("gespeichert")
        newvals = self.dbinst.getNewOrChanged(laststored)

        # special case images, store them first in gphotos
        newImgs = newvals[self.baseJS["db_tabellenname"] + "_images"]
        newImgs, photo_objs = self.storeImages(newImgs)
        imgCnt = len(newImgs)
        newvals[self.baseJS["db_tabellenname"] + "_images"] = newImgs

        recCnt = 0
        self.message("Speichere Daten")
        for sheet_name in newvals.keys():
            vals = newvals[sheet_name]
            if len(vals) > 0:
                recCnt += len(vals)
                self.gsheet.appendValues(sheet_name, vals)
        self.setConfigValue("gespeichert", time.strftime("%Y.%m.%d %H:%M:%S"))
        for obj in photo_objs:
            os.remove(obj["filepath"])
        self.msgDialog("Gespeichert",
                       f"Es wurden {imgCnt} Fotos und {recCnt} neue oder geänderte Datensätze gespeichert")
        self.dbinst.deleteAll()
        self.show_markers()

    def center_on(self, lat, lon):
        self.mapview.set_zoom_at(17, 0, 0, 2.0)
        self.mapview.center_on(lat, lon)
        self.mapview.centerlat = lat
        self.mapview.centerlon = lon
        self.relocated = 0

    def map_relocated(self):
        self.relocated += 1

    def centerLatLon(self):
        # if self.relocated == 1, the map has not moved since the last center_on
        if self.relocated == 1:
            return (self.mapview.centerlat, self.mapview.centerlon)
        return (self.mapview.lat, self.mapview.lon)

    def gps_onlocation(self, **kwargs):
        lat = kwargs["lat"]
        lon = kwargs["lon"]
        self.center_on(float(lat), float(lon))
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
        self.pushScreen("Images")
        self.images.show_images()

    def show_daten(self, delay):
        if self.checkAlias():
            self.daten.setDaten()
            self.center_on(self.daten.lat, self.daten.lon)
            if delay and self.root.sm.current_screen.name == "Karte":
                Clock.schedule_once(self.show_daten2, 1)
            else:
                self.pushScreen("Daten")

    def show_daten2(self, *args):
        self.pushScreen("Daten")

    def on_pause(self):
        print("on_pause")
        lat, lon = self.centerLatLon()
        self.store.put("latlon", lat=lat, lon=lon)
        return True

    def on_stop(self):
        print("on_stop")
        return self.on_pause()

    def on_resume(self):
        print("on_resume")
        # base = self.store.get("base")["base"]
        # self.setup(base)
        return True

    def change_base(self, *args):
        self.dialog_dismiss()
        items = self.items
        for item in items:
            if item.ids.check.active:
                t = item.text
                if t != self.selected_base:
                    self.setup(t)
                    return

    def show_bases(self, *args):
        basen = list(self.baseConfig.getNames())
        items = [ItemConfirm(text=base) for base in basen]
        x = basen.index(self.selected_base)
        for i, item in enumerate(items):
            items[i].ids.check.active = i == x
        self.items = items
        buttons = [MDFlatButton(text="OK", text_color=self.theme_cls.primary_color, on_press=self.change_base)]
        if self.dialog is not None:
            self.dialog_dismiss()
        self.dialog = MDDialog(size_hint=(.8, .4), type="confirmation", title="Auswahl der Datenbasis",
                               text="Bitte Datenbasis auswählen",
                               items=items, buttons=buttons)
        self.dialog.auto_dismiss = False  # this line costed me two hours! Without, change_base is not called!
        self.dialog.open()

    def set_icon(self, instance_check, x):
        instance_check.active = True
        check_list = instance_check.get_widgets(instance_check.group)
        for check in check_list:
            if check != instance_check:
                check.active = False

    def createMarker(self, lat, lon):
        img = self.dbinst.existsImage(lat, lon)
        if self.baseJS.get("name") == "Abstellanlagen":
            col = self.dbinst.getRedYellowGreen(lat, lon)
        elif self.dbinst.existsDatenOrZusatz(lat, lon):
            col = "red"
        else:
            col = None
        if not img and col is None:
            return None
        if col is None:
            col = "red"
        if img:
            src = col + "_plus48.png"
        else:
            src = col + "48.png"
        mm = MyMapMarker(lat=lat, lon=lon, source=utils.getCurDir() + "/icons/" + src)
        return mm

    def add_marker(self, lat, lon):
        lat_round = round(lat, self.stellen)
        lon_round = round(lon, self.stellen)
        markerMapKey = str(lat_round) + ":" + str(lon_round)
        markerOld = self.markerMap.get(markerMapKey, None)
        markerNew = self.createMarker(lat_round, lon_round)
        if markerOld is not None:
            self.mapview.remove_marker(markerOld)
        if markerNew is None:
            del self.markerMap[markerMapKey]
        else:
            self.mapview.add_marker(markerNew)
            self.markerMap[markerMapKey] = markerNew

    def clickMarker(self, marker):
        self.curMarker = marker
        self.center_on(marker.lat, marker.lon)
        self.show_daten(True)

    def do_capture(self, *args):
        if self.checkAlias():  # and self.root.sm.current_screen.name == "Daten":
            self.daten.setDaten()
            self.kamera.do_capture(self.daten.lat, self.daten.lon)

    def checkAlias(self):
        if not self.account.ids.aliasname.text:
            self.msgDialog("Account", "Bitte den Aliasnamen ausfüllen")
            self.pushScreen("Account")
            return False
        self.dbinst.aliasname = self.account.ids.aliasname.text
        return True

    def show_error(self, *args):
        self.msgDialog("Konfigurationsfehler", self.error)

    def pushScreen(self, nextScreen):
        self.lastScreen = self.root.sm.current_screen.name
        self.root.sm.current = nextScreen

    def popScreen(self, window, key, *largs):
        if key != 27:
            return True
        if self.lastScreen is None:
            if self.dialog is not None:
                self.dialog_dismiss()
            self.dialog = MDDialog(size_hint=(.8, .4), title="Beenden?", text="Möchten Sie die App beenden?",
                                   buttons=[
                                       MDFlatButton(
                                           text="Ja", text_color=self.theme_cls.primary_color,
                                           on_press=self.stopApp),
                                       MDFlatButton(
                                           text="Nein", text_color=self.theme_cls.primary_color,
                                           on_press=self.dialog_dismiss),
                                   ])
            self.dialog.auto_dismiss = False  # !!!
            self.dialog.open()
        else:
            self.root.sm.current = self.lastScreen
            self.lastScreen = None
        return True

    # see https://www.youtube.com/watch?v=oQdGWeN51EE
    def build_config(self, config):
        config.setdefaults('Locations', {
            # 'boolexample': True,
            # 'numericexample': 10,
            # 'stringexample': 'somestring',
            # 'optionsexample': 'options2',
            # 'pathexample': 'c:/temp',
            'gespeichert': '',
            'maxdim': 1024,
        })

    def build_settings(self, settings):
        settings_json = json.dumps([
            {'type': 'title',
             'title': 'Einstellungen'},
            {'type': 'string',
             'title': 'Gespeichert',
             'desc': 'Datum des letzten Speicherns',
             'section': 'Locations',
             'key': 'gespeichert'},
            {'type': 'numeric',
             'title': 'Max Dim',
             'desc': 'Max photo size from Goggle Photos',
             'section': 'Locations',
             'key': 'maxdim'},
            # {'type': 'bool',
            #  'title': 'A boolean setting',
            #  'desc': 'Boolean description text',
            #  'section': 'Locations',
            #  'key': 'boolexample'},
            # {'type': 'numeric',
            #  'title': 'A numeric setting',
            #  'desc': 'Numeric description text',
            #  'section': 'Locations',
            #  'key': 'numericexample'},
            # {'type': 'options',
            #  'title': 'An options setting',
            #  'desc': 'Options description text',
            #  'section': 'Locations',
            #  'key': 'optionsexample',
            #  'options': ['option1', 'option2', 'option3']},
            # {'type': 'path',
            #  'title': 'A path setting',
            #  'desc': 'Path description text',
            #  'section': 'Locations',
            #  'key': 'pathexample'}
        ])

        settings.add_json_panel('Locations', self.config, data=settings_json)

    def on_config_change(self, config, section, key, value):
        print(config, section, key, value)

    def getConfigValue(self, param, fallback=""):
        return self.config.get("Locations", param, fallback=fallback)

    def setConfigValue(self, param, value):
        self.config.set("Locations", param, value)
        self.config.write()

    def stopApp(self, *args):
        if self.future is not None and not self.future.done():
            self.msgDialog("Bitte warten", "Das Speichern ist noch nicht beendet!")
            return
        self.stop()

    @mainthread
    def message(self, m):
        toast(m)

    def spinnerStart(self):
        self.spinner.active = True
        if self.spinner.parent is not None:
            self.spinner.parent.remove_widget(self.spinner)
        self.root.sm.current_screen.add_widget(self.spinner)

    def spinnerStop(self):
        self.spinner.active = False
        if self.spinner.parent is not None:
            self.spinner.parent.remove_widget(self.spinner)

if __name__ == "__main__":
    # nc = True
    # x = MyMapMarker(lat=0, lon=0, nocache=nc)
    # print("size1", utils.getsize(x))
    # y = []
    # for i in range(100):
    #     y.append(MyMapMarker(lat=0, lon=0, nocache=nc))
    # print("size100", utils.getsize(y))
    # Cache.print_usage()

    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = Locations()

    bugs.fixBugs()
    if platform == "android":
        app.run()
    else:
        import cProfile
        import pstats

        cProfile.run("app.run()", "cprof.prf")
        with open("cprof.txt", "w") as cprf:
            p = pstats.Stats("cprof.prf", stream=cprf)
            p.strip_dirs().sort_stats("cumulative").print_stats(20)
