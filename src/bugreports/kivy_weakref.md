###Problems with "ReferenceError: weakly-referenced object no longer exists" analyzed a bit further and fixed temporarily
There is a large amount of ReferenceErrors described on the net, e.g. https://github.com/kivy/kivy/issues/2768 or
https://github.com/kivy/kivy/issues/6779. There is even a video: https://www.youtube.com/watch?v=EAaOz8z-P3U.

The recommended fix is often to second the weak
reference with a normal reference, so that the weak reference stays alive.
This seems to defeat the purpose of weak references. You can then as well take
normal references. Apparently, a dead method should simply not be called,
instead of raising an exception, right?

Looking at is_dead in weakmethod.py, it seemed to me that this function should 
not throw a reference error at all, just return True for a dead reference. But
I wanted also to find out where the dead reference comes from. Issue 6779 
contains a description on how to "pin point the widget that is causing a 
ReferenceError". 

I was also plagued by this error on Android. On Windows, I saw it very 
rarely, on Android, it came very quickly and made the app unusable.
I came finally up with this code:
```
class WeakMethod:
    '''Implementation of a
    `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
    for functions and bound methods.
    '''
    def __init__(self, method):
        self.method = None
        self.method_name = None
        try:
            call_frames = inspect.stack()
            self.stacktrace= "\n".join([">>>  " + os.path.basename(t.filename) 
                + ":" + str(t.lineno) + " " + t.function for t in call_frames[1:]])
            self.called_method = method.__func__.__name__
            if method.__self__ is not None:
                self.method_name = method.__func__.__name__
                self.proxy = weakref.proxy(method.__self__)
            else:
                self.method = method
                self.proxy = None
        except AttributeError:
            self.method = method
            self.proxy = None

    def do_nothing(self,*args):
        print("do_nothing instead of method ", self.called_method, "generated in:")
        print(self.stacktrace)

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
            print("Callback ", self.called_method, " no longer exists, generated in:")
            print(self.stacktrace)
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
```
 In __init__, a stacktrace is saved, and the method name. In is_dead, the
 ReferenceError is caught, the stacktrace is output and True is returned.
 Otherwise, I did not change the condition `(bool(dir(self.proxy))`, 
 but, as it raises an exception, it should be replaced by something that does 
 not, I suppose weakref.peek. Then, in \_\_call\_\_, I call do_nothing 
 for a dead method. However, I never saw this happen.
 
 What I saw instead, was masses of these stacktraces:
```
 I/python: Callback  _animate_color  no longer exists, generated in:
 I/python: >>>  clock.py:560 tick
 I/python: >>>  base.py:339 idle
 I/python: >>>  window_sdl2.py:479 _mainloop
 I/python: >>>  window_sdl2.py:747 mainloop
 I/python: >>>  base.py:504 runTouchApp
 I/python: >>>  app.py:855 run
 I/python: >>>  main.py:576 <module>

 I/python: Callback  _anim  no longer exists, generated in:
 I/python: >>>  clock.py:560 tick
 I/python: >>>  base.py:339 idle
 I/python: >>>  window_sdl2.py:479 _mainloop
 I/python: >>>  window_sdl2.py:747 mainloop
 I/python: >>>  base.py:504 runTouchApp
 I/python: >>>  app.py:855 run
 I/python: >>>  main.py:576 <module>
```

Note that the call to inspect.stack makes the program much slower!

I found that I could do nothing about the dead references to anim and
animate_color. But the option to simpy not call dead functions did also 
not work. The app would simply freeze after some time. I guess some
weak methods should not be weak. So I took the brute-force-approach to 
eliminate weak references for the time being altogether. 
This is easily done by substituting the line
```
self.proxy = weakref.proxy(method.__self__)
```
in \_\_init\_\_ with
```
self.proxy = method.__self__ 
```

#### Workaround technique 
I could easily change the code in the package, when running my program on the desktop. 
On Android, however, I could not find out what must be done, to change 
the code in one of the required packages, Below .buildozer, there are a 
couple of directories containing kivy code, plus some zip files, plus 
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
class WeakMethod:
    '''Implementation of a
    `weakref <http://en.wikipedia.org/wiki/Weak_reference>`_
    for functions and bound methods.
    '''
    def __init__(self, method):
        self.method = None
        self.method_name = None
        try:
            #call_frames = inspect.stack()
            #self.stacktrace= "\n".join([">>>  " + os.path.basename(t.filename) + ":" + str(t.lineno) + " " + t.function for t in call_frames[1:]])
            #self.called_method = method.__func__.__name__
            if method.__self__ is not None:
                self.method_name = method.__func__.__name__
                self.proxy = method.__self__ # weakref.proxy(method.__self__)
            else:
                self.method = method
                self.proxy = None
        except AttributeError:
            self.method = method
            self.proxy = None

    def do_nothing(self,*args):
        print("do_nothing instead of method ", self.called_method, "generated in:")
        print(self.stacktrace)

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
            print("Callback ", self.called_method, " no longer exists, generated in:")
            print(self.stacktrace)
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

def fixBugs():
    import kivy.weakmethod as wm

    wm.WeakMethod.is_dead = WeakMethod.is_dead
    wm.WeakMethod.__init__ = WeakMethod.__init__
    wm.WeakMethod.__call__ = WeakMethod.__call__
    wm.WeakMethod.do_nothing = WeakMethod.do_nothing

```

It is probably difficult to analyze a problem that has so much to do with the
unpredictable behaviour of the garbage collector. But the ReferenceError really
plagues many people!

