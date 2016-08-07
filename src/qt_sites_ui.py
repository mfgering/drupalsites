# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/mgering/git/drupalsites/src/qt_sites_ui.ui'
#
# Created: Wed Jan 27 14:06:45 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ManageDialog(object):
    def setupUi(self, ManageDialog):
        ManageDialog.setObjectName("ManageDialog")
        ManageDialog.resize(576, 794)
        self.gridLayout = QtGui.QGridLayout(ManageDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtGui.QLabel(ManageDialog)
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_3 = QtGui.QLabel(ManageDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 1, 1, 1)
        self.optionListWidget = QtGui.QListWidget(ManageDialog)
        self.optionListWidget.setObjectName("optionListWidget")
        self.gridLayout.addWidget(self.optionListWidget, 1, 0, 2, 1)
        self.allSitesCheckBox = QtGui.QCheckBox(ManageDialog)
        self.allSitesCheckBox.setObjectName("allSitesCheckBox")
        self.gridLayout.addWidget(self.allSitesCheckBox, 1, 1, 1, 1)
        self.sitesListWidget = QtGui.QListWidget(ManageDialog)
        self.sitesListWidget.setObjectName("sitesListWidget")
        self.gridLayout.addWidget(self.sitesListWidget, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(ManageDialog)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.label = QtGui.QLabel(ManageDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 5, 0, 1, 1)
        self.msgsTextBrowser = QtGui.QTextBrowser(ManageDialog)
        self.msgsTextBrowser.setObjectName("msgsTextBrowser")
        self.gridLayout.addWidget(self.msgsTextBrowser, 6, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(ManageDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 2)
        self.opListWidget = QtGui.QListWidget(ManageDialog)
        self.opListWidget.setObjectName("opListWidget")
        self.gridLayout.addWidget(self.opListWidget, 4, 0, 1, 2)

        self.retranslateUi(ManageDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ManageDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ManageDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ManageDialog)

    def retranslateUi(self, ManageDialog):
        ManageDialog.setWindowTitle(QtGui.QApplication.translate("ManageDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ManageDialog", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Options</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ManageDialog", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Sites</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.allSitesCheckBox.setText(QtGui.QApplication.translate("ManageDialog", "All", None, QtGui.QApplication.UnicodeUTF8))
        self.sitesListWidget.setSortingEnabled(False)
        self.label_4.setText(QtGui.QApplication.translate("ManageDialog", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Operations</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ManageDialog", "<html><head/><body><p><span style=\" font-size:12pt; font-weight:600;\">Messages</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

