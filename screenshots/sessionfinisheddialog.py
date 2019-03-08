# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from qgis.utils import iface
from screenshots import sessionFromName


class SessionFinishedDialog(QDialog):

    def __init__(self, session):
        super(SessionFinishedDialog, self).__init__(iface.mainWindow())
        self.reopen = False
        self.session = session
        self.setWindowTitle("Session finished")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setMargin(10)
        txt = "<p>Congratulations! You have correctly finished this session.</p>"

        if session.nextSessions:
            txt += "<p>We recommend you the following sessions to continue:</p><ul>"
            for i, nextSession in enumerate(session.nextSessions):
                txt+="<li><a href='%i'>%s</a>" % (i, nextSession[1])

        txt += "</ul><p>If you don't want to run more sessions, just <a href='exit'>close this dialog.</a></p>"
        txt += "<p>If you want to run another session, click <a href='reopen'>here</a> to reopen the session selector</p>"

        self.text = QTextBrowser()
        self.text.anchorClicked.connect(self.linkClicked)
        self.text.setHtml(txt)
        self.text.setOpenLinks(False)
        self.verticalLayout.addWidget(self.text)
        self.setLayout(self.verticalLayout)
        self.resize(400, 300)
        self.nextSession = None

    def linkClicked(self, url):
        if url.path() not in ["exit", "reopen"]:
            self.nextSession = sessionFromName(*self.session.nextSessions[int(url.path())])
        if url.path() =="reopen":
            self.reopen = True
        self.close()
