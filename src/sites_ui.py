#!/usr/bin/python
'''
Created on Jan 25, 2016

@author: mgering
'''
import sys
from PySide.QtCore import *
from PySide.QtGui import *
from qt_sites_ui import *
from drupalsites import *

class MyManageDialog(QDialog, Ui_ManageDialog):
  def __init__(self, parent=None):
    QDialog.__init__(self)
    super(Ui_ManageDialog, self).__init__(parent)
    self.__index = 0
    self.setupUi(self)
    self.update()
    
    item = QtGui.QListWidgetItem(self.optionListWidget)
    self.verbose_check = QtGui.QCheckBox('verbose')
    self.optionListWidget.setItemWidget(item, self.verbose_check)
    item = QtGui.QListWidgetItem(self.optionListWidget)
    self.dry_run_check = QtGui.QCheckBox('dry run')
    self.optionListWidget.setItemWidget(item, self.dry_run_check)
    
    self.allSitesCheckBox.clicked.connect(self.all_sites_clicked)
    for site in sorted(sites):
      item = QtGui.QListWidgetItem(self.sitesListWidget)
      check = QtGui.QCheckBox(site)
      self.sitesListWidget.setItemWidget(item, check)
    for op in sorted(Operations):
      item = QtGui.QListWidgetItem(self.opListWidget)
      radio = QtGui.QRadioButton(op)
      radio.setToolTip(Operations[op].desc)
      self.opListWidget.setItemWidget(item, radio)
  
  def all_sites_clicked(self):
    print "Clicked"
    pass
  
if __name__ == '__main__':
  # Create a Qt application
  app = QApplication(sys.argv)
  dlg = MyManageDialog()
  dlg.show()
  
  # Create a Label and show it
#   label = QLabel("Hello World")
#   label.show()
  # Enter Qt application main loop
  app.exec_()
  sys.exit()
