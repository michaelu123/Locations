import inspect
import os
import weakref

from kivy.uix.widget import Widget

tracing = False

class WeakMethod:
    '''Implementation of a
    `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
    for functions and bound methods.
    '''
    def __init__(self, method):
        self.method = None
        self.method_name = None
        try:
            if tracing:
                call_frames = inspect.stack()
                self.stacktrace= "\n".join([">>>  " + os.path.basename(t.filename) + ":" + str(t.lineno) + " " + t.function for t in call_frames[1:]])
            self.called_method = method.__func__.__name__
            if method.__self__ is not None:
                self.method_name = method.__func__.__name__
                self.proxy = weakref.proxy(method.__self__)  # method.__self__
            else:
                self.method = method
                self.proxy = None
        except AttributeError:
            self.method = method
            self.proxy = None

    def do_nothing(self,*args):
        if tracing:
            print("do_nothing instead of method", self.called_method, "generated in:")
            print(self.stacktrace)
        else:
            print("do_nothing instead of method", self.called_method)

    def __call__(self):
        '''Return a new bound-method like the original, or the
        original function if it was just a function or unbound
        method.
        Returns None if the original object doesn't exist.
        '''
        try:
            if self.proxy:
                return getattr(self.proxy, self.method_name)
        except ReferenceError:
            pass
        return self.do_nothing if self.method is None else self.method

    def is_dead(self):
        '''Returns True if the referenced callable was a bound method and
        the instance no longer exists. Otherwise, return False.
        '''
        try:
            return self.proxy is not None and not bool(dir(self.proxy))
        except ReferenceError:
            if tracing:
                print("Callback ", self.called_method, " no longer exists, generated in:")
                print(self.stacktrace)
            else:
                print("Callback ", self.called_method, " no longer exists")
            return True

    def __eq__(self, other):
        try:
            if type(self) is not type(other):
                return False
            s = self()
            return s is not None and s == other()
        except:
            return False

    def __repr__(self):
        return '<WeakMethod proxy={} method={} method_name={}>'.format(
               self.proxy, self.method, self.method_name)


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
    import kivy.weakmethod as wm

    #print(dir(wm))
    #print(dir(wm.WeakMethod))
    wm.WeakMethod.is_dead = WeakMethod.is_dead
    wm.WeakMethod.__init__ = WeakMethod.__init__
    wm.WeakMethod.__call__ = WeakMethod.__call__
    wm.WeakMethod.do_nothing = WeakMethod.do_nothing

    import kivy_garden.mapview as mv
    mv.MapView.on_transform = MapView.on_transform


