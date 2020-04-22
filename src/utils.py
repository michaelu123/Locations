import os
import sys
import traceback


def printEx(msg, e):
    print(msg, e)
    traceback.print_exc(file=sys.stdout)


def getDataDir():
    if os.name == "posix":
        # Context.getExternalFilesDir()
        return "/storage/emulated/0/Android/data/de.adfc-muenchen.abstellanlagen/files"
    return "."
