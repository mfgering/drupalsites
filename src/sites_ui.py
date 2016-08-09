#!/usr/bin/python
'''
Created on Jan 25, 2016

@author: mgering
'''
import sys
import drupalsites
import PySide.QtCore
import PySide.QtGui
from qt_sites_ui import *

class QtOperationOutput(drupalsites.OperationOutput):
  
  def __init__(self, widget):
    super(QtOperationOutput, self).__init__()
    self.widget = widget
  
  def write(self, msg):
    self.widget.emit([msg.rstrip()])
  
class SitesOpWorker(PySide.QtCore.QObject):
  def __init__(self):
    super(SitesOpWorker, self).__init__()
    self.start.connect(self.perform)
    self.operation_output =  QtOperationOutput(self.progress)
    drupalsites.set_operation_output(self.operation_output)
  
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
    site = drupalsites.sites[site_name]
    operation = site.get_operation(op_name)
    drupalsites.set_verbose(verbose_opt)
    
    if dry_run_opt:
      msgs.append("Dry run for operation {} on site {}".format(operation.name, site.name))
    else:
      operation.do_cmd()
    return {'msgs': msgs}

class MyManageDialog(PySide.QtGui.QDialog, Ui_ManageDialog):
  def __init__(self, parent=None):
    PySide.QtGui.QDialog.__init__(self)
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
    for site in sorted(drupalsites.sites):
      item = QtGui.QListWidgetItem(self.sitesListWidget)
      check = QtGui.QCheckBox(site)
      check.setObjectName(site)
      self.site_checkboxes.append(check)
      self.sitesListWidget.setItemWidget(item, check)
    self.op_radios = []
    for op in sorted(drupalsites.Site.operations):
      item = QtGui.QListWidgetItem(self.opListWidget)
      radio = QtGui.QRadioButton(op)
      radio.setToolTip(drupalsites.Site.operations[op].desc)
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
    apply_button = self.buttonBox.button(PySide.QtGui.QDialogButtonBox.Apply)
    apply_button.setEnabled(False)
    self.worker.start.emit(sites, op, verbose_opt, dry_run_opt)
  
  def worker_progress(self, msgs):
    self.msgsTextBrowser.append("\n".join(msgs))
  
  def worker_finished(self, msg):
    self.msgsTextBrowser.append(msg)
    apply_button = self.buttonBox.button(PySide.QtGui.QDialogButtonBox.Apply)
    apply_button.setEnabled(True)
  

if __name__ == '__main__':
  # Create a Qt application
  app = PySide.QtGui.QApplication(sys.argv)
  dlg = MyManageDialog()
  dlg.show()
  
  # Create a Label and show it
#   label = QLabel("Hello World")
#   label.show()
  # Enter Qt application main loop
  app.exec_()
  sys.exit()
