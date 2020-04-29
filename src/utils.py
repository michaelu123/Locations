import io
import os
import sys
import time
import traceback

from kivy.uix.popup import Popup

photo_image_path = "/photo_camera-black.png"


class MsgPopup(Popup):
    def __init__(self, msg):
        super().__init__()
        self.ids.message_label.text = msg


def printEx(msg, e):
    print(msg, e)
    traceback.print_exc(file=sys.stdout)


def printExToString(msg, e, tracebk=False):
    output = io.StringIO()
    print(msg, ":", e, file=output)
    if tracebk:
        traceback.print_exc(file=output)
    s = output.getvalue()
    output.close()
    return s


def getDataDir():
    if os.name == "posix":
        # Context.getExternalFilesDir()
        return "/storage/emulated/0/Android/data/de.adfc-muenchen.abstellanlagen/files"
    return "."

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

def walk(p):
    print("walk", p)
    try:
        if os.path.isdir(p):
            for cp in sorted(os.listdir(p)):
                walk(p + "/" + cp)
    except Exception as e:
        print("walk", p, ":", e)



