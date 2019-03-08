# -*- coding: utf-8 -*-

from builtins import range

import os
import codecs
from functools import partial

import markdown

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QCoreApplication, QUrl, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QTextDocument
from qgis.PyQt.QtWidgets import QListWidgetItem, QMessageBox, QListWidget, QAbstractItemView
from qgis.utils import iface

from screenshots.utils import execute
from screenshots.session import Step
from screenshots.sessionfinisheddialog import SessionFinishedDialog

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "sessionwidget.ui"))


class SessionWidget(BASE, WIDGET):

    sessionFinished = pyqtSignal(bool)

    def __init__(self, session):
        super(SessionWidget, self).__init__()
        self.setupUi(self)
        self.listHeight = self.listSteps.height()
        self.btnFinish.clicked.connect(self.finishSession)
        self.btnMove.clicked.connect(self.stepFinished)
        self.btnRestart.clicked.connect(self.restartSession)
        self.btnRunStep.clicked.connect(self.runCurrentStepFunction)
        self.init(session)

    def init(self, session):
        self.resetGui()
        self.listSteps.clear()
        self.session = session
        bulletIcon = QIcon(os.path.dirname(__file__) + "/bullet.png")
        for step in session.steps:
            item = QListWidgetItem(step.name)
            self.listSteps.addItem(item)
            item.setHidden(step.steptype == Step.AUTOMATEDSTEP)
            item.setIcon(bulletIcon)
        self.currentStep = 0
        self.sessionNameLabel.setText("<b>Current session:</b> {}".format(session.name))
        self.btnMove.setText(self.tr("Next step"))
        self.btnMove.setToolTip(self.tr("Move to next step"))
        self.moveToNextStep()

    def runCurrentStepFunction(self):
        QCoreApplication.processEvents()
        step = self.session.steps[self.currentStep]
        self.webView.setEnabled(False)
        step.runFunction("function")
        self.webView.setEnabled(True)
        self.stepFinished()

    def stepFinished(self):
        step = self.session.steps[self.currentStep]
        if step.endcheck is not None:
            ret = step.runFunction("endcheck")
            if ret != True:
                # We support both bool and str return values, for backwards compatibility
                if ret == False:
                    msg = ("It seems that the previous step was not correctly completed."
                            "\nPlease review and complete the instructions before moving"
                            "\nto the next step.")
                else:
                    msg = ret
                QMessageBox.warning(self, "Session", msg)
                return
        item = self.listSteps.item(self.currentStep)
        item.setBackground(Qt.white)
        if step.endsignals is not None:
            for i, sig in enumerate(step.endsignals):
                sig.disconnect(self.listeners[i])
        self.currentStep += 1
        self.moveToNextStep()

    def endSignalEmitted(self, i):
        def _endSignalEmitted(i, *args):
            step = self.session.steps[self.currentStep]
            if step.endsignalchecks is None or step.endsignalchecks[i](*args):
                self.stepFinished()

        return partial(_endSignalEmitted, i)

    def restartSession(self):
        self.resetGui()
        for i in range(self.listSteps.count()):
            item = self.listSteps.item(i)
            item.setBackground(Qt.white)
        self.currentStep = 0
        self.moveToNextStep()

    def moveToNextStep(self):
        if self.currentStep == len(self.session.steps):
            dlg = SessionFinishedDialog(self.session)
            dlg.exec_()
            if dlg.nextSession is not None:
                self.init(dlg.nextSession)
            else:
                self.finishSession(dlg.reopen)
        else:
            if self.currentStep == len(self.session.steps) - 1:
                self.btnMove.setText(self.tr("Finish"))
                self.btnMove.setToolTip(self.tr("Finish the session"))

            step = self.session.steps[self.currentStep]
            if step.endsignals is not None:
                self.listeners  = []
                for i, sig in enumerate(step.endsignals):
                    self.listeners.append(self.endSignalEmitted(i))
                    sig.connect(self.listeners[-1])
            item = self.listSteps.item(self.currentStep)
            item.setBackground(Qt.green)
            self.listSteps.scrollToItem(item, QAbstractItemView.PositionAtCenter)
            if os.path.exists(step.description):
                with codecs.open(step.description, encoding="utf-8") as f:
                    html = f.read()
                if step.description.endswith(".md"):
                    html = markdown.markdown(html)
                html = self.session.style + html
                self.webView.document().setMetaInformation(QTextDocument.DocumentUrl,
                                                           QUrl.fromUserInput(step.description).toString())
                self.webView.setHtml(html)
            else:
                self.webView.setHtml(step.description)

            height = self.webView.document().size().height()
            if height > self.webView.height():
                self.listSteps.setFixedHeight(self.listHeight)
            else:
                self.listSteps.setFixedHeight(self.listSteps.minimumHeight())

            QCoreApplication.processEvents()
            if step.prestep is not None:
                step.runFunction("prestep")
            if step.function is not None:
                self.btnRunStep.setEnabled(step.steptype != Step.AUTOMATEDSTEP)
                self.btnMove.setEnabled(step.steptype != Step.AUTOMATEDSTEP and step.endsignals is None)
                if step.steptype == Step.AUTOMATEDSTEP:
                    self.runCurrentStepFunction()
            else:
                self.btnRunStep.setEnabled(False)
                self.btnMove.setEnabled(step.endsignals is None)

    def finishSession(self, reopen):
        self.setVisible(False)

        self.sessionFinished.emit(reopen)

    def resetGui(self):
        self.btnMove.setText(self.tr("Next step"))
        self.btnMove.setToolTip(self.tr("Move to next step"))
