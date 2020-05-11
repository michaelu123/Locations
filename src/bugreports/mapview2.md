After some more hours of poking around, I first had to realize that the random zoom had not been entirely defeated, as I had thought.
In the end, I substituted in all comparisons of floats with a constant the float with its rounded value.
bugs.py now reads:
```
import kivy.weakmethod as wm
import kivy_garden.mapview as mv
from kivy.uix.widget import Widget
class MapView(Widget):
    def on_touch_up(self, touch):
        if touch.grab_current == self:
            touch.ungrab(self)
            self._touch_count -= 1
            if self._touch_count == 0:
                # animate to the closest zoom
                zoom, scale = self._touch_zoom
                cur_zoom = self.zoom
                cur_scale = self._scale
                if cur_zoom < zoom or round(cur_scale, 2) < scale:
                    self.animated_diff_scale_at(1.0 - cur_scale, *touch.pos)
                elif cur_zoom > zoom or round(cur_scale, 2) > scale:
                    self.animated_diff_scale_at(2.0 - cur_scale, *touch.pos)
                self._pause = False
            return True
        return super(mv.MapView, self).on_touch_up(touch)

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
        if round(scale, 2) >= 2.0:
            zoom += 1
            scale /= 2.0
        elif round(scale, 2) < 1.0:
            zoom -= 1
            scale *= 2.0
        zoom = clamp(zoom, map_source.min_zoom, map_source.max_zoom)
        if zoom != self._zoom:
            self.set_zoom_at(zoom, scatter.x, scatter.y, scale=scale)
            self.trigger_update(True)
        else:
            if zoom == map_source.min_zoom and round(scatter.scale, 2) < 1.0:
                scatter.scale = 1.0
                self.trigger_update(True)
            else:
                self.trigger_update(False)

        if map_source.bounds:
            self._apply_bounds()
        self._transform_lock = False
        self._scale = self._scatter.scale

    @property
    def scale(self):
        if self._invalid_scale:
            self._invalid_scale = False
            self._scale = round(self._scatter.scale, 2)
        return self._scale


def fixBugs():
    mv.MapView.on_touch_up = MapView.on_touch_up
    mv.MapView.on_transform = MapView.on_transform
    mv.MapView.scale = MapView.scale
```

Note the various calls to round(). Interestingly, I had to replace in on_touch_up the final call of
```
return super().on_touch_up(touch)
```
with
```
return super(mv.MapView, self).on_touch_up(touch)
```
otherwise the super()-call failed with the message
TypeError: super(type, obj): obj must be an instance or subtype of type

The whole rounding is certainly a hack, but apparently mapview needs some more consideration for floating 
point accuracy. I hope someone who knows what he does (as opposed to me, I am just guessing, 
using trial and error) eventually comes up with a clean solution.


