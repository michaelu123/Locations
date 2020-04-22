import locale
import os
import os.path
import sqlite3
import time
from sqlite3 import OperationalError

from kivy.base import runTouchApp
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.app import MDApp

from src import utils

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
            left_action_items: [['account', app.showMenu]]
            right_action_items: [['email', app.senden],['delete', app.clear]]
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
                text: "Foto"
                size_hint: 1/4,1
                on_release: pass
            MDRaisedButton:
                text: "Daten"
                size_hint: 1/4,1
                on_release: pass
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


class Abstellanlagen(MDApp):
    def build(self):
        if os.name == "posix":
            from plyer.platforms.android.gps import AndroidGPS
            perms = ["android.permission.READ_EXTERNAL_STORAGE",
                     "android.permission.WRITE_EXTERNAL_STORAGE",
                     "android.permission.access_fine_location"]
            haveperms = acquire_permissions(perms)
            gps = AndroidGPS()
            gps.configure(app.gps_onlocation, app.gps_on_status)
            Clock.schedule_once(gps.start, 5)

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
        self.mapview = self.root.ids.sm.current_screen.ids.mapview
        self.mapview.map_source.min_zoom = 11
        self.mapview.map_source.bounds = (11.4, 48.0, 11.8, 48.25)
        return self.root

    def showMenu(self):
        pass

    def senden(self):
        pass

    def clear(self):
        pass

    def center(self, lat, lon):
        self.mapview.center_on(lat, lon)

    def gps_onlocation(self, **kwargs):
        lat = kwargs["lat"]
        lon = kwargs["lon"]
        print("onloc lat", lat, lon)
        self.mapview.center_on(float(lat), float(lon))

    def gps_onstatus(self, **kwargs):
        print("onsta", **kwargs)


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
        for perm in permissions:
            r = activity.checkCurrentPermission(perm)
            if r == 0:
                return False
        return True

    haveperms = allgranted(permissions)
    if haveperms:
        # we have the permission and are ready
        return True

    # invoke the permissions dialog
    activity.requestPermissions(permissions)

    # now poll for the permission (UGLY but we cant use android Activity's onRequestPermissionsResult)
    t0 = time.time()
    while time.time() - t0 < timeout and not haveperms:
        # in the poll loop we could add a short sleep for performance issues?
        haveperms = allgranted(permissions)
        time.sleep(1)

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
