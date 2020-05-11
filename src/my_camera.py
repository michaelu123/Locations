import android
import android.activity as activity1
from os import remove
from jnius import autoclass, cast
from plyer.facades import Camera
from plyer.platforms.android import activity as activity2

Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
MediaStore = autoclass('android.provider.MediaStore')
#Uri = autoclass('android.net.Uri')
Fileprovider = autoclass("androidx.core.content.FileProvider")
File = autoclass("java.io.File")


class MyAndroidCamera(Camera):

    def _take_picture(self, on_complete, filename=None):
        assert(on_complete is not None)
        self.on_complete = on_complete
        self.filename = filename
        activity1.unbind(on_activity_result=self._on_activity_result)
        activity1.bind(on_activity_result=self._on_activity_result)
        intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
        # OLD: uri = Uri.parse('file://' + filename)

        app_context = activity2.getApplication().getApplicationContext()
        uri = Fileprovider.getUriForFile(app_context, "de.adfcmuenchen.fileprovider", File(filename))
        print("filepath3", filename, uri, uri.toString())
        #content://de.adfcmuenchen.fileprovider/external/Android/data/de.adfc-muenchen.abstellanlagen/files/20200424_....jpg
        # same as /data/user/0/de.adfcmuenchen.abstellanlagen/files/IMG_20200424_....png
        app_context.grantUriPermission("de.adfcmuenchen", uri, Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
        parcelable = cast('android.os.Parcelable', uri)
        intent.putExtra(MediaStore.EXTRA_OUTPUT, parcelable)
        activity2.startActivityForResult(intent, 0x123)

    # def _take_video(self, on_complete, filename=None):
    #     assert(on_complete is not None)
    #     self.on_complete = on_complete
    #     self.filename = filename
    #     activity.unbind(on_activity_result=self._on_activity_result)
    #     activity.bind(on_activity_result=self._on_activity_result)
    #     intent = Intent(MediaStore.ACTION_VIDEO_CAPTURE)
    #     uri = Uri.parse('file://' + filename)
    #     parcelable = cast('android.os.Parcelable', uri)
    #     intent.putExtra(MediaStore.EXTRA_OUTPUT, parcelable)
    #
    #     # 0 = low quality, suitable for MMS messages,
    #     # 1 = high quality
    #     intent.putExtra(MediaStore.EXTRA_VIDEO_QUALITY, 1)
    #     activity.startActivityForResult(intent, 0x123)

    def _on_activity_result(self, requestCode, resultCode, intent):
        if requestCode != 0x123:
            return
        activity1.unbind(on_activity_result=self._on_activity_result)
        if self.on_complete(self.filename):
            self._remove(self.filename)

    def _remove(self, fn):
        try:
            remove(fn)
        except OSError:
            pass
