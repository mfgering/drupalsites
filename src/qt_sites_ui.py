# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/mgering/git/drupalsites/src/qt_sites_ui.ui'
#
# Created: Mon Jan 25 17:14:10 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ManageDialog(object):
    def setupUi(self, ManageDialog):
        ManageDialog.setObjectName("ManageDialog")
        ManageDialog.resize(423, 733)
        self.buttonBox = QtGui.QDialogButtonBox(ManageDialog)
        self.buttonBox.setGeometry(QtCore.QRect(20, 680, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        self.optionsGroupBox = QtGui.QGroupBox(ManageDialog)
        self.optionsGroupBox.setGeometry(QtCore.QRect(20, 20, 171, 201))
        self.optionsGroupBox.setObjectName("optionsGroupBox")
        self.optionListWidget = QtGui.QListWidget(self.optionsGroupBox)
        self.optionListWidget.setGeometry(QtCore.QRect(0, 30, 151, 171))
        self.optionListWidget.setObjectName("optionListWidget")
        self.sitesGroupBox = QtGui.QGroupBox(ManageDialog)
        self.sitesGroupBox.setGeometry(QtCore.QRect(200, 20, 201, 231))
        self.sitesGroupBox.setObjectName("sitesGroupBox")
        self.allSitesCheckBox = QtGui.QCheckBox(self.sitesGroupBox)
        self.allSitesCheckBox.setGeometry(QtCore.QRect(0, 30, 161, 21))
        self.allSitesCheckBox.setObjectName("allSitesCheckBox")
        self.sitesListWidget = QtGui.QListWidget(self.sitesGroupBox)
        self.sitesListWidget.setGeometry(QtCore.QRect(0, 50, 191, 151))
        self.sitesListWidget.setObjectName("sitesListWidget")
        self.operationsGroupBox = QtGui.QGroupBox(ManageDialog)
        self.operationsGroupBox.setGeometry(QtCore.QRect(20, 230, 381, 201))
        self.operationsGroupBox.setObjectName("operationsGroupBox")
        self.opListWidget = QtGui.QListWidget(self.operationsGroupBox)
        self.opListWidget.setGeometry(QtCore.QRect(0, 30, 371, 192))
        self.opListWidget.setObjectName("opListWidget")
        self.msgsTextBrowser = QtGui.QTextBrowser(ManageDialog)
        self.msgsTextBrowser.setGeometry(QtCore.QRect(20, 471, 381, 181))
        self.msgsTextBrowser.setObjectName("msgsTextBrowser")
        self.label = QtGui.QLabel(ManageDialog)
        self.label.setGeometry(QtCore.QRect(30, 450, 66, 17))
        self.label.setObjectName("label")

        self.retranslateUi(ManageDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ManageDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ManageDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ManageDialog)

    def retranslateUi(self, ManageDialog):
        ManageDialog.setWindowTitle(QtGui.QApplication.translate("ManageDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.optionsGroupBox.setTitle(QtGui.QApplication.translate("ManageDialog", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.sitesGroupBox.setTitle(QtGui.QApplication.translate("ManageDialog", "Sites", None, QtGui.QApplication.UnicodeUTF8))
        self.allSitesCheckBox.setText(QtGui.QApplication.translate("ManageDialog", "All", None, QtGui.QApplication.UnicodeUTF8))
        self.sitesListWidget.setSortingEnabled(False)
        self.operationsGroupBox.setTitle(QtGui.QApplication.translate("ManageDialog", "Operations", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ManageDialog", "Messages", None, QtGui.QApplication.UnicodeUTF8))

