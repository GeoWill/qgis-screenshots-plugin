# -*- coding: utf-8 -*-

from builtins import str
from builtins import range
import os
import codecs
from collections import defaultdict

import markdown

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon, QTextDocument, QCursor
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QDialogButtonBox, QFileDialog, QMessageBox, QApplication

try:
    from qgis.utils import Qgis
except:
    from qgis.utils import QGis as Qgis

from screenshots import sessions, _removeSession, groups, installSessionsFromZipFile

WIDGET, BASE = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "sessionselector.ui"))


class SessionSelector(BASE, WIDGET):

    def __init__(self):
        super(SessionSelector, self).__init__()
        self.setupUi(self)

        self.session = None

        self.fillTree()

        self.sessionsTree.itemDoubleClicked.connect(self.itemDoubleClicked)

        self.btnRunSession.setDefault(True)
        self.btnRunSession.clicked.connect(self.okPressed)
        self.btnRemove.clicked.connect(self.remove)
        self.btnClose.clicked.connect(self.close)
        self.btnAdd.clicked.connect(self.addSessions)

        self.btnRemove.setEnabled(False)

        self.sessionsTree.currentItemChanged.connect(self.currentItemChanged)

        try:
            self.sessionsTree.setCurrentItem(self.sessionsTree.invisibleRootItem().child(0).child(0))
        except AttributeError:
            self.currentItemChanged()

    def fillTree(self):
        allSessions = defaultdict(list)
        for session in sessions:
            allSessions[session.group].append(session)

        self.sessionsTree.clear()
        sessionIcon = QIcon(os.path.dirname(__file__) + "/session.gif")
        for group, groupSessions in list(allSessions.items()):
            groupItem = QTreeWidgetItem()
            groupItem.setText(0, group)
            groupItem.description = groups.get(group, "")
            for session in groupSessions:
                sessionItem = QTreeWidgetItem()
                sessionItem.session = session
                sessionItem.setText(0, session.name)
                sessionItem.setIcon(0, sessionIcon)
                groupItem.addChild(sessionItem)
                if session.version[0] is not None and str(session.version[0]) > QGis.QGIS_VERSION:
                    sessionItem.setText(0, session.name + " (requires QGIS >= {})".format(session.version[0]))
                    sessionItem.setDisabled(True)
                if session.version[1] is not None and str(session.version[1]) < QGis.QGIS_VERSION:
                    sessionItem.setText(0, session.name + " (requires QGIS <= {})".format(session.version[1]))
                    sessionItem.setDisabled(True)
            self.sessionsTree.addTopLevelItem(groupItem)

        self.sessionsTree.sortItems(0, 0)

        self.sessionsTree.expandAll()

    def itemDoubleClicked(self, item, i):
        if hasattr(item, "session"):
            self.session = item.session
            self.close()

    def currentItemChanged(self):
        item = self.sessionsTree.currentItem()
        if item:
            if hasattr(item, "session"):
                self.btnRemove.setText("Uninstall session")
                self.btnRemove.setEnabled(True)
                self.btnRunSession.setEnabled(True)
                if os.path.exists(item.session.description):
                    with codecs.open(item.session.description, encoding="utf-8") as f:
                        html = "".join(f.readlines())
                        if item.session.description.endswith(".md"):
                            html = markdown.markdown(html)
                    self.webView.document().setMetaInformation(QTextDocument.DocumentUrl,
                                                               QUrl.fromUserInput(item.session.description).toString())
                    self.webView.setHtml(html)
                else:
                    self.webView.setHtml("<p>{}</p>".format(item.session.description))
            else:
                self.btnRunSession.setEnabled(False)
                self.btnRemove.setText("Uninstall sessions group")
                self.btnRemove.setEnabled(True)
                if os.path.exists(item.description):
                    with codecs.open(item.description, encoding="utf-8") as f:
                        html = "".join(f.readlines())
                    if item.description.endswith(".md"):
                        html = markdown.markdown(html)
                    self.webView.document().setMetaInformation(QTextDocument.DocumentUrl,
                                                               QUrl.fromUserInput(item.description).toString())
                else:
                    html = item.description
                self.webView.setHtml(html)

        else:
            self.btnRemove.setEnabled(False)
            self.btnRunSession.setEnabled(False)

    def addSessions(self):
        ret, __ = QFileDialog.getOpenFileName(self, "Select sessions ZIP file" , "", '*.zip')
        if ret:
            try:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                installSessionsFromZipFile(ret)
                self.fillTree()
            finally:
                QApplication.restoreOverrideCursor()

    def remove(self):
        item = self.sessionsTree.currentItem()
        if hasattr(item, "session"):
            reply = QMessageBox.question(None,
                                     "Confirmation",
                                     "Are you sure you want to uninstall this session?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
            if reply == QMessageBox.Yes:
                _removeSession(item.session)
                item = self.sessionsTree.currentItem()
                parent = item.parent()
                parent.takeChild(parent.indexOfChild(item))
                if parent.childCount() == 0:
                    self.sessionsTree.takeTopLevelItem(self.sessionsTree.indexOfTopLevelItem(parent))
                item.session.uninstall()
        else:
            reply = QMessageBox.question(None,
                         "Confirmation",
                         "Are you sure you want to uninstall this group of sessions?",
                         QMessageBox.Yes | QMessageBox.No,
                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                for i in range(item.childCount()):
                    child = item.child(i)
                    _removeSession(child.session)
                    child.session.uninstall()
                self.sessionsTree.takeTopLevelItem(self.sessionsTree.indexOfTopLevelItem(item))

    def okPressed(self):
        self.session = self.sessionsTree.selectedItems()[0].session
        self.close()
