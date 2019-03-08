# -*- coding: utf-8 -*-


from qgis.PyQt.QtGui import QScreen
from qgis.core import QgsApplication
from pathlib import Path


class Screenshot(object):
    """docstring for Screenshot
    screenshot = Screenshot()
    screenshot.saveDirectory = 'path/to/directory/for/shots'
    screenshot.screen()
    """
    def __init__(self):
        super(Screenshot, self).__init__()
        self._screen=QgsApplication.instance().primaryScreen()
        self.iscreenshot = 0

    @property
    def screen(self):
        return self._screen

    @screen.setter
    def screen(self, widget=None):
        if not widget:
            self._screen=QgsApplication.instance().primaryScreen()
        elif isinstance(widget, QWidget):
            self._screen = widget.windowHandle().screen()
        else:
            TypeError("Widget should be QWidget or None.")

    @property
    def saveDirectory(self):
        return self._saveDirectory

    @saveDirectory.setter
    def saveDirectory(self, dirName):
        self._saveDirectory = Path(dirName)
        if not self.saveDirectory.exists():
            self.saveDirectory.mkdir(parents=True)


    def takeScreenshot(self, widget):
        pixmap = self.screen.grabWindow(widget.winId()).copy()
        saveScreenshot(pixmap)

    def saveScreenshot(self, pixmap, name=self.iScreenshot, directory=self.saveDirectory):
        savePath = saveDirectory + Path('{}.png'.format(self.iScreenshot))
        pixmap.save(savePath, 'png')
        QgsApplication.messagelog().logMessage("Screenshot saved to {}".format(savePath))
        self.iScreenshot += 1


