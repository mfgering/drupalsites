#!/usr/bin/python
'''
Created on Jan 25, 2016

@author: mgering
'''
import sys
import time
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

class SitesOpWorker(QObject):
  def __init__(self):
    super(SitesOpWorker, self).__init__()
    self.start.connect(self.perform)
  
  start = QtCore.Signal(list, str, bool, bool)
  finished = QtCore.Signal(str)
  progress = QtCore.Signal(list)
  
  def perform(self, sites, op_name, verbose_opt, dry_run_opt):
    errors = 0
    msgs = []
    if op_name == '':
      self.progress.emit(["<span style='color: red;'><b>Please select an operation.</b></span>"])
      errors += 1
    if len(sites) == 0:
      self.progress.emit(["<span style='color: red;'><b>Please select at least one site.</b></span>"])
      errors += 1
    if errors == 0:
      self.progress.emit(["<b>Starting...</b>"])
      for site_name in sites:
        result = self.perform_site_op(site_name, op_name, verbose_opt, dry_run_opt)
        msgs = result['msgs']
        self.progress.emit(msgs);
    self.finished.emit("<b>... Done!</b>")
    
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
    
    self.site_op_thread = QtCore.QThread()
    self.site_op_thread.start()
    self.worker = SitesOpWorker()
    self.worker.moveToThread(self.site_op_thread)
    self.finished.connect(self.stop_thread)
    self.worker.finished.connect(self.worker_finished)
    self.worker.progress.connect(self.worker_progress)
#     self.site_op_thread.started.connect(worker.perform)
    
  def stop_thread(self):
    self.site_op_thread.quit()
    
  def all_sites_clicked(self):
    for site_box in self.site_checkboxes:
      site_box.setCheckState(self.allSitesCheckBox.checkState())
  
  def apply(self):
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
    apply_button = self.buttonBox.button(QDialogButtonBox.Apply)
    apply_button.setEnabled(False)
    self.worker.start.emit(sites, op, verbose_opt, dry_run_opt)
  
  def worker_progress(self, msgs):
    self.msgsTextBrowser.append("\n".join(msgs))
  
  def worker_finished(self, msg):
    self.msgsTextBrowser.append(msg)
    apply_button = self.buttonBox.button(QDialogButtonBox.Apply)
    apply_button.setEnabled(True)
  

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
