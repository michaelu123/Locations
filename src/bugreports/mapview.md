#### Two bugs in mapview

The following program demonstrates two bugs in mapview. 
My mapview version is 0.104.
Python is at 3.7.

```
from kivy.base import runTouchApp
from kivy.lang import Builder

if __name__ == '__main__' and __package__ is None:
    from os import sys, path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

root = Builder.load_string(
    """
#:import MapSource kivy_garden.mapview.MapSource

<Toolbar@BoxLayout>:
    size_hint_y: None
    height: '48dp'
    padding: '4dp'
    spacing: '4dp'

    canvas:
        Color:
            rgba: .2, .2, .2, .6
        Rectangle:
            pos: self.pos
            size: self.size

<ShadedLabel@Label>:
    size: self.texture_size
    canvas.before:
        Color:
            rgba: .2, .2, .2, .6
        Rectangle:
            pos: self.pos
            size: self.size

RelativeLayout:

    MapView:
        id: mapview
        lat: 48.13724404
        lon: 11.57617109
        zoom: 16
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

        # next line enabled causes infinite loop
        #on_map_relocated: mapview.sync_to(self)

        MapMarker: # Fischbrunnen
            #size: 40,40
            lat: 48.13724404
            lon: 11.57617109
            on_press: mapview.center_on(self.lat, self.lon)

    Toolbar:
        top: root.top
        Button:
            text: "Center"
            on_release: mapview.center_on(48.13724404, 11.57617109)
        Spinner:
            text: "mapnik"
            values: MapSource.providers.keys()
            on_text: mapview.map_source = self.text

    Toolbar:
        Label:
            text: "Zoom: {}".format(mapview.zoom)
        Label:
            text: "Longitude: {}".format(mapview.lon)
        Label:
            text: "Latitude: {}".format(mapview.lat)
    """
)

root.ids.mapview.map_source.bounds = (11.5, 48.1, 11.6, 48.2)
root.ids.mapview.map_source.min_zoom = 15
runTouchApp(root)
```

The first bug is a random zoom, when the map is moved in high zoom levels. 
It is also issued in https://github.com/kivy-garden/mapview/issues/22 . 
This one is easy to fix. I noticed that the zoom changed when scale was 
a little bit larger than 2.0, e.g. 2.00000004. In view.py/on_transform replace
```
        if scale >= 2.0:
            zoom += 1
            scale /= 2.0
        elif scale < 1:
            zoom -= 1
            scale *= 2.0
```
with
```
        if scale >= 2.01:
            zoom += 1
            scale /= 2.0
        elif scale < 0.99:
            zoom -= 1
            scale *= 2.0
```
The second bug I was unable to fix, because the interaction 
between Scatter and Mapview remains a mystery for me. The problem shows 
normally in high zoom level, and it occurs randomly. When you press the 
"Center" button, the map moves consistently to the "Fischbrunnen" at 
Marienplatz, Munich. When you however move the map, so that the marker is 
outside of the center, and click on the marker, the marker does often not move 
back to the center. This may require a few attempts to reproduce. It is easiest
to reproduce when you zoom to level 19, click the Center Button, move the map 
so that the marker is near the upper right corner, and click it. Often, the 
map moves erratically and sometimes zooms out. This behaviour seems to be 
dependent on the mouse position when the marker is clicked. When we center 
the map with the "Center"-Button, the mouse is outside of the Scatter,
and this seems to be the reason why this center always succeeds.

In the error case, 
do_update gets called many times, where the scale grows slowly from 1 to 2.
Maybe floating point precision plays a role here. But then there is the random 
behaviour of the bug, which may have to do with the unforeseeable times, 
in which the Clock calls the scheduled callbacks.

#### Workaround technique 
I could easily change the code in the package, when running my program on the desktop. 
On Android, however, I could not find out what must be done, to change 
the code in one of the required packages, Below .buildozer, there are a 
couple of directories containing mapview code, plus some zip files, plus 
some .pyc files, and nothing I did caused the app to run the modified code.
Here I describe a workaround:

In main.py, between the App construction and app.run, call bugs.fixBugs()
```
    app = MyApp()
    import bugs
    bugs.fixBugs()
    app.run()
```    
bugs.py contains this code:
```
from kivy.uix.widget import Widget

def clamp(x, minimum, maximum):
    y = max(minimum, min(x, maximum))
    return y

class MapView(Widget):
    def on_transform(self, *args):
        self._invalid_scale = True
        if self._transform_lock:
            return
        self._transform_lock = True
        # recalculate viewport
        map_source = self.map_source
        zoom = self._zoom
        scatter = self._scatter
        scale = scatter.scale
        #MUHif scale >= 2.0:
        if scale > 2.01:
            zoom += 1
            scale /= 2.0
        #MUH elif scale < 1.0:
        elif scale < 0.99:
            zoom -= 1
            scale *= 2.0
        zoom = clamp(zoom, map_source.min_zoom, map_source.max_zoom)
        if zoom != self._zoom:
            self.set_zoom_at(zoom, scatter.x, scatter.y, scale=scale)
            self.trigger_update(True)
        else:
            if zoom == map_source.min_zoom and scatter.scale < 1.0:
                scatter.scale = 1.0
                self.trigger_update(True)
            else:
                self.trigger_update(False)

        if map_source.bounds:
            self._apply_bounds()
        self._transform_lock = False
        self._scale = self._scatter.scale

def fixBugs():
    import kivy_garden.mapview as mv
    mv.MapView.on_transform = MapView.on_transform

```

 