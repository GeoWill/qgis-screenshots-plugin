# -*- coding: utf-8 -*-

from __future__ import absolute_import

from builtins import str
import os
import imp
import glob
import site
import zipfile

site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/extlibs'))

from qgis.PyQt.QtCore import QDir
from qgis.core import QgsApplication, QgsMessageLog

from screenshots.session import sessionFromYamlFile
from screenshots.utils import screenshotsBaseFolder

sessions = []
groups = {}


def addGroup(name, description):
    global groups
    groups[name] = description


def _addSession(toAdd):
    for session in sessions:
        if session.name == toAdd.name and session.group == toAdd.group:
            return
    sessions.append(toAdd)


def _removeSession(toRemove):
    for session in sessions[::-1]:
        if session.name == toRemove.name and session.group == toRemove.group:
            sessions.remove(session)


def addSessionModule(module):
    if "session" in dir(module):
        _addSession(module.session)


def removeSessionModule(module):
    if "session" in dir(module):
        _removeSession(module.session)


def isPackage(folder, subfolder):
    path = os.path.join(folder, subfolder)
    return os.path.isdir(path) and glob.glob(os.path.join(path, "__init__.py*"))


def isYamlSessionFolder(folder, subfolder):
    path = os.path.join(folder, subfolder)
    return os.path.isdir(path) and glob.glob(os.path.join(path, "session.yaml"))


def addSessionsFolder(folder, pluginName):
    packages = [x for x in os.listdir(folder) if os.path.isdir(os.path.join(folder, x))]
    for p in packages:
        try:
            tokens = folder.split(os.sep)
            moduleTokens = tokens[tokens.index(pluginName):] + [p]
            moduleName = ".".join(moduleTokens)
            m = __import__(moduleName, fromlist="dummy")
            addSessionModule(m)
        except Exception as e:
            QgsMessageLog.logMessage("Can not add sessions folder {}:\n{}".format(folder, str(e)), "Sessions")

    folders = [x for x in os.listdir(folder) if isYamlSessionFolder(folder, x)]
    for f in folders:
        session = sessionFromYamlFile(os.path.join(folder, f, "session.yaml"))
        if session:
            _addSession(session)


def removeSessionsFolder(folder, pluginName):
    packages = [x for x in os.listdir(folder) if isPackage(folder, x)]
    for p in packages:
        try:
            tokens = folder.split(os.sep)
            moduleTokens = tokens[tokens.index(pluginName):] + [p]
            moduleName = ".".join(moduleTokens)
            m = __import__(moduleName, fromlist="dummy")
            removeSessionModule(m)
        except Exception as e:
            QgsMessageLog.logMessage("Can not remove sessions folder {}:\n{}".format(folder, str(e)), "Sessions")

    folders = [x for x in os.listdir(folder) if isYamlSessionFolder(folder, x)]
    for f in folders:
        session = sessionFromYamlFile(os.path.join(folder, f, "session.yaml"))
        if session:
            _removeSession(session)


def sessionFromName(group, name):
    for session in sessions:
        if session.group == group and session.name == name:
            return session


# maintained this fuction to does not change plugin api from external calls
# it can be substituted directly with screenshotsBaseFolder()
def sessionsFolder():
    return screenshotsBaseFolder()


def installSessionsFromZipFile(path):
    group = os.path.basename(path).split(".")[0]
    with zipfile.ZipFile(path, "r") as z:
        folder = os.path.join(sessionsFolder(), group)
        if not QDir(folder).exists():
            QDir().mkpath(folder)
        z.extractall(folder)

        loadSessions()


def loadSessionsFromPaths(paths):
    hasErrors = False
    for path in paths:
        for folder in os.listdir(path):
            if os.path.isdir(os.path.join(path, folder)):
                groupFiles = [os.path.join(path, folder, f) for f in ["group.html", "group.md"]]
                for groupFile in groupFiles:
                    if os.path.exists(groupFile):
                        groups[folder.replace("_", " ")] = groupFile
                        break

                for subfolder in os.listdir(os.path.join(path, folder)):
                    if os.path.isdir(os.path.join(path, folder, subfolder)):
                        try:
                            f = os.path.join(path, folder, subfolder, "__init__.py")
                            if os.path.exists(f):
                                m = imp.load_source("{}.{}".format(folder, subfolder), f)
                                addSessionModule(m)
                        except Exception as e:
                            QgsMessageLog.logMessage("Can not load session from {}:\n{}".format(f, str(e)), "Sessions")
                            hasErrors = True

                        if isYamlSessionFolder(os.path.join(path, folder), subfolder):
                            session = sessionFromYamlFile(os.path.join(path, folder, subfolder, "session.yaml"))
                            if session:
                                _addSession(session)
                            else:
                                hasErrors = True
    return hasErrors


def loadSessions():
    """Load all sessions belonging to the plugin or installed
    in the configured session location path.
    """
    paths = []
    # set local sessions path
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "_sessions"))
    if QDir(folder).exists():
        paths.append(folder)

    # set configured session location
    paths.append(sessionsFolder())

    return loadSessionsFromPaths(paths)


def classFactory(iface):
    from .plugin import ScreenshotsPlugin
    return ScreenshotsPlugin(iface)
