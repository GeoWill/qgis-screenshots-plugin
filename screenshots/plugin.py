# -*- coding: utf-8 -*-

from builtins import object

import os
import webbrowser
import shutil

from qgis.PyQt.QtCore import Qt, QDir
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsApplication

from qgiscommons2.gui import (addAboutMenu,
                             removeAboutMenu,
                             addHelpMenu,
                             removeHelpMenu)
from qgiscommons2.gui.settings import (addSettingsMenu,
                                      removeSettingsMenu)
from qgiscommons2.settings import readSettings

import screenshots
from screenshots.sessionwidget import SessionWidget
from screenshots.sessionselector import SessionSelector
from screenshots.utils import execute


class ScreenshotsPlugin(object):

    def __init__(self, iface):
        self.iface = iface
        readSettings()

        try:
            from qgistester.tests import addTestModule
            from screenshots.test import testerplugin
            addTestModule(testerplugin, "Screenshots")
        except Exception as e:
            pass

        self.sessionWidget = None

    def initGui(self):
        sessionIcon = QIcon(os.path.dirname(__file__) + "/Screenshots.gif")
        self.action = QAction(sessionIcon, "Open Sessions Library...", self.iface.mainWindow())
        self.action.triggered.connect(self.start)
        self.iface.addPluginToMenu("Screenshots", self.action)

        addSettingsMenu("Screenshots")
        addHelpMenu("Screenshots")
        addAboutMenu("Screenshots")

        self.sessionwidget = None

        hasErrors = screenshots.loadSessions()
        if hasErrors:
            QMessageBox.warning(self.iface.mainWindow(),
                                "Screenshots",
                                "Some sessions were not loaded. Check QGIS log for more details")

    def unload(self):
        self.iface.removePluginMenu("Screenshots", self.action)
        del self.action

        removeSettingsMenu("Screenshots")
        removeHelpMenu("Screenshots")
        removeAboutMenu("Screenshots")

        tempDir = os.path.join(QDir.tempPath(), "screenshots" , "session")
        if QDir(tempDir).exists():
            shutil.rmtree(tempDir, True)

        try:
            from qgistester.tests import removeTestModule
            from screenshots.test import testerplugin
            removeTestModule(testerplugin, "Screenshots")
        except Exception as e:
            pass

    def start(self):
        if self.sessionWidget is not None:
            QMessageBox.warning(self.iface.mainWindow(), "Session", "A session is currently being run")
            return

        dlg = SessionSelector()
        dlg.exec_()
        if dlg.session:
            self.sessionWidget = SessionWidget(dlg.session)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.sessionWidget)
            def sessionFinished(reopen):
                self.sessionWidget = None
                execute(dlg.session.cleanup)
                if reopen:
                    self.start()
            self.sessionWidget.sessionFinished.connect(sessionFinished)

