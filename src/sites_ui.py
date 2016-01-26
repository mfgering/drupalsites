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
from __builtin__ import xrange
from contextlib import contextmanager
import StringIO
from web_drupalsites import perform_site_op

@contextmanager
def stdout_redirector(stream):
    old_stdout = sys.stdout
    sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout

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
    self.site_checkboxes = []
    for site in sorted(sites):
      item = QtGui.QListWidgetItem(self.sitesListWidget)
      check = QtGui.QCheckBox(site)
      check.setObjectName(site)
      self.site_checkboxes.append(check)
      self.sitesListWidget.setItemWidget(item, check)
    self.op_radios = []
    for op in sorted(Operations):
      item = QtGui.QListWidgetItem(self.opListWidget)
      radio = QtGui.QRadioButton(op)
      radio.setToolTip(Operations[op].desc)
      self.op_radios.append(radio)
      self.opListWidget.setItemWidget(item, radio)
    self.buttonBox.button(QtGui.QDialogButtonBox.Apply).clicked.connect(self.apply)
  
  def all_sites_clicked(self):
    print "Clicked"
    pass
  
  def apply(self):
    print "Apply"
    sites = []
    for check in self.site_checkboxes:
      state = check.checkState()
      if state == QtCore.Qt.CheckState.Checked:
        sites.append(check.text())
    op = None
    for radio in self.op_radios:
      if radio.isChecked():
        op = radio.text()
        break;
    verbose_opt = self.verbose_check.checkState()
    dry_run_opt = self.dry_run_check.checkState()
    self.msgsTextBrowser.clear()
    if not op is None:
      for site_name in sites:
        result = self.perform_site_op(site_name, op, verbose_opt, dry_run_opt)
        self.msgsTextBrowser.append("\n".join(result['msgs']))
        print result;
        
  def perform_site_op(self, site_name, op_name, verbose_opt, dry_run_opt):
    msgs = []
    site = sites[site_name]
    operation_cls = Operations[op_name]
    operation = operation_cls(site)
    set_verbose(verbose_opt)
    if dry_run_opt:
      msgs.append("Dry run for operation {} on site {}".format(operation.name, site.name))
    else:
      std_str = StringIO.StringIO()
      with stdout_redirector(std_str):
        operation.do_cmd()
        msg = std_str.getvalue()
        msgs.append(msg)
        std_str.close()
    return {'msgs': msgs}

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
