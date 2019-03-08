# -*- coding: utf-8 -*-

from builtins import str
from builtins import range
from builtins import object

import os
import traceback
import yaml
import difflib
import shutil
import codecs
import imp
from importlib import import_module

from qgis.core import QgsMessageLog

from screenshots.utils import openProject, menuFromName, execute, getMenuPaths, qgisLocale


def _ensureList(obj):
    if obj is None or isinstance(obj, list):
        return obj
    else:
        return [obj]


class Step(object):

    MANUALSTEP, AUTOMATEDSTEP = list(range(2))

    def __init__(self, name, description, function=None, prestep=None, params=None, endsignals=None,
                 endsignalchecks=None, endcheck=lambda:True, steptype=1):
        self.name = name
        self.description = description or ""
        self.function = function
        self.prestep = prestep
        self.endcheck = endcheck
        self.endsignals = _ensureList(endsignals)
        self.endsignalchecks = _ensureList(endsignalchecks)
        self.steptype = steptype
        self.params = params

    def runFunction(self, func):
        params = self.getParams(func)

        if func == "function":
            return self.function(*params)
        elif func == "prestep":
            return self.prestep(*params)
        elif func == "endcheck":
            return self.endcheck(*params)

    def getParams(self, func):
        if func in self.params:
            return self.params[func]
        else:
            return tuple()


class Session(object):

    def __init__(self, name, group, description, folder = None, version = [None,None]):
        if folder is None:
            folder = os.path.dirname(traceback.extract_stack()[-2][0])
        self.folder = folder
        self.steps = []
        self.name = name
        self.group = group
        self.cleanup = lambda: None
        self.version = version
        self.nextSessions = []
        self.description = self.resolveFile(description)
        self.style = ""
        path = os.path.join(os.path.dirname(self.folder), "style.css")
        if os.path.exists(path):
            with codecs.open(path, encoding="utf-8") as f:
                self.style = "<style>\n" + f.read() + "\n</style>\n"
        path = os.path.join(self.folder, "project.qgs")
        if os.path.exists(path):
            self.addStep("Open project", "Open project", lambda: openProject(path))

    def setCleanup(self,function):
        self.cleanup = function

    def addNextSession(self, group, name):
        self.nextSessions.append((group,name))

    def resolveFile(self, f):
        if f is None:
            f = ""
        else:
            if not os.path.exists(f):
                for i in [qgisLocale(), "en", ""]:
                    path = os.path.join(self.folder, i, f)
                    if os.path.exists(path):
                        return path

        return os.path.join(self.folder, f)

    def addStep(self, name, description, function=None, prestep=None, endsignals=None,
                endsignalchecks=None, endcheck=lambda:True, steptype=1):
        description = self.resolveFile(description)

        params = dict()
        if function is not None:
            if isinstance(function, dict):
                if "params" in function:
                    p = tuple(function["params"])
                else:
                    p = None
                params["function"] = p

                if function["name"].startswith("utils."):
                    functionName = function["name"].split(".")[1]
                    function = getattr(import_module('sessions.utils'), functionName)
                else:
                    mod = imp.load_source('functions', os.path.join(self.folder, "functions.py"))
                    function = getattr(mod, function["name"])

                _function = function
            else:
                _function = function
        else:
            _function = None

        if prestep is not None:
            if isinstance(prestep, dict):
                if "params" in prestep:
                    p = tuple(prestep["params"])
                else:
                    p = None
                params["prestep"] = p

                if prestep["name"].startswith("utils."):
                    functionName = prestep["name"].split(".")[1]
                    function = getattr(import_module("sessions.utils"), functionName)
                else:
                    mod = imp.load_source("functions", os.path.join(self.folder, "functions.py"))
                    function = getattr(mod, function["name"])

                _prestep = function
            else:
                _prestep = prestep
        else:
            _prestep = None

        if endcheck is not None:
            if isinstance(endcheck, dict):
                if "params" in endcheck:
                    p = tuple(endcheck["params"])
                else:
                    p = None
                params["endcheck"] = p

                if endcheck["name"].startswith("utils."):
                    functionName = endcheck["name"].split(".")[1]
                    function = getattr(import_module("sessions.utils"), functionName)
                else:
                    mod = imp.load_source('functions', os.path.join(self.folder, "functions.py"))
                    function = getattr(mod, endcheck["name"])

                _endcheck = function
            else:
                _endcheck = endcheck
        else:
            _endcheck = None

        step = Step(name, description, _function, _prestep, params, endsignals, endsignalchecks, _endcheck, steptype)
        self.steps.append(step)

    def addMenuClickStep(self, menuName, description=None, name=None):
        try:
            menu, action = menuFromName(menuName)
        except:
            closest = difflib.get_close_matches(menuName, getMenuPaths())
            if closest:
                menu, action = menuFromName(closest[0])
            else:
                QgsMessageLog.logMessage("Session '{}' contains a wrong menu name: '{}'".format(self.name, menuName),
                                         "Sessions")
                return None
        if name is None:
            name = "Click on '{}' menu item.".format(action.text().replace("&",""))
        if description is None:
            description = "<p>Click on <b>{}</b> menu item.</p>" \
                          "<p>Once you click, the session will " \
                          "automatically move to the next step.</p>".format(menuName.replace("/"," > "))

        def checkMenu(triggeredAction):
            return triggeredAction.text() == action.text()

        self.addStep(name, description, None, None, menu.triggered, checkMenu, None, Step.MANUALSTEP)

    def uninstall(self):
        shutil.rmtree(self.folder, True)


def sessionFromYamlFile(f):
    locale = qgisLocale()

    with codecs.open(f, encoding="utf-8") as stream:
        sessionDict = yaml.load(stream)

    if locale in sessionDict["session"]:
        sessionDict = sessionDict["session"][locale]
    else:
        if "en" in sessionDict["session"]:
            sessionDict = sessionDict["session"]["en"]
        else:
            sessionDict = sessionDict["session"]

    session = Session(sessionDict["name"], sessionDict["group"], sessionDict["description"],
                    os.path.dirname(f), sessionDict.get("version", [None, None]))
    for step in sessionDict["steps"]:
        if "menu" in step:
            if "description" in step:
                description = step["description"]
            else:
                description = None

            if "name" in step:
                name = step["name"]
            else:
                name = None

            session.addMenuClickStep(step["menu"], description, name)

        else:
            if "function" in step:
                function = step["function"]
            else:
                function = None

            if "prestep" in step:
                prestep = step["prestep"]
            else:
                prestep = None

            if "endcheck" in step:
                _endcheck = step["endcheck"]
            else:
                _endcheck = None

            try:
                session.addStep(step["name"], step["description"], function, prestep, endcheck=_endcheck, steptype=Step.MANUALSTEP)
            except Exception as e:
                QgsMessageLog.logMessage("Can not load session from {}:\n{}".format(f, str(e)), "Sessions")
                return None

    if "nextSessions" in sessionDict:
        for nextSession in sessionDict["nextSessions"]:
            session.addNextSession(nextSession["group"], nextSession["name"])
    return session
