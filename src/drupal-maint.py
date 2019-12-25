#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.8.3 on Tue Dec 24 15:27:38 2019
#

import logging, sys, threading
import wx
import drupalsites

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class MyFrame(wx.Frame):
	def __init__(self, *args, **kwds):
		# begin wxGlade: MyFrame.__init__
		kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
		wx.Frame.__init__(self, *args, **kwds)
		self.SetSize((625, 680))
		self.checkbox_verbose = wx.CheckBox(self, wx.ID_ANY, "verbose")
		self.checkbox_dry_run = wx.CheckBox(self, wx.ID_ANY, "dry run")
		self.checkbox_all_sites = wx.CheckBox(self, wx.ID_ANY, "All")
		self.panel_site_list = wx.Panel(self, wx.ID_ANY)
		self.radio_box_ops_copy_copy = OpsRadioBox(self, wx.ID_ANY)
		self.text_ctrl_log = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_MULTILINE | wx.TE_READONLY)
		self.button_start = wx.Button(self, wx.ID_ANY, "Start")
		self.button_stop = wx.Button(self, wx.ID_ANY, "Stop")
		self.frame_statusbar = self.CreateStatusBar(1)

		self.__set_properties()
		self.__do_layout()

		self.Bind(wx.EVT_CHECKBOX, self.on_all_sites, self.checkbox_all_sites)
		# end wxGlade

		self.status_timer = None
		try:
			# redirect text here
			redir = RedirectText(self.text_ctrl_log, threading.current_thread().ident)
			sys.stdout = redir
			sys.stderr = redir
			self.worker_thread = None
			self.gui_thread_id = threading.current_thread().ident
			#self.args = self.parseArgs()
			self.set_button_states()
			self.SetMinClientSize((600, 480))
			self.SetClientSize((600, 480))
			self.init_sites_panel()
			self.init_operations_panel()
		except Exception as exc:
			self.set_status("Error: "+str(exc))
			logging.getLogger().exception(exc)
		print("App starting")

	def init_sites_panel(self):
		for site in drupalsites.sites:
			site_name = drupalsites.sites[site].name
			checkbox = wx.CheckBox(self, wx.ID_ANY, site_name)
			checkbox.site_name = site_name
			self.Bind(wx.EVT_CHECKBOX, self.on_sites_checkbox, checkbox)
			self.sizer_sites.Add(checkbox, 0, 0, 0)

	def init_operations_panel(self):
		for op_class in drupalsites.OperationClasses:
			pass

	def set_button_states(self):
		options_ok = self.options_ok()
		sites = self.get_sites_selected()
		no_sites_msg = "No sites selected"
		if len(sites) == 0:
			self.set_status(no_sites_msg)
		else:
			txt = self.GetStatusBar().GetStatusText()
			if txt == no_sites_msg:
				self.set_status("")
		start = options_ok and len(sites) > 0 and \
				(self.worker_thread is None or \
				self.worker_thread.done)
		stop = self.worker_thread is not None and \
				not self.worker_thread.done
		self.button_start.Enable(start)
		self.button_stop.Enable(stop)

	def options_ok(self):
		return True

	def get_sites_selected(self):
		sites = []
		for cbox in self.get_site_checkboxes():
			if cbox.IsChecked():
				sites.append(cbox.site_name)
		return sites

	def set_status(self, msg, timeout=-1, timeout_msg=None):
		if self.status_timer is not None:
			del self.status_timer
			self.status_timer = None
		self.GetStatusBar().SetStatusText(msg)
		if timeout > 0:
			self.status_timeout_msg = timeout_msg
			threadId = threading.current_thread().ident
			if self.guiThreadId == threadId:
				self.status_timer = wx.CallLater(timeout, self.status_timed_out, msg=timeout_msg)
			else:
				wx.CallAfter(wx.CallLater, timeout, self.status_timed_out, msg=timeout_msg)			

	def status_timed_out(self, msg=None):
		if self.status_timer is not None:
			if msg is None:
				msg = ""
			self.GetStatusBar().SetStatusText(msg)
			del self.status_timer
			self.status_timer = None

	def __set_properties(self):
		# begin wxGlade: MyFrame.__set_properties
		self.SetTitle("Drupal Site Maintenance")
		self.frame_statusbar.SetStatusWidths([-1])
		
		# statusbar fields
		frame_statusbar_fields = [" "]
		for i in range(len(frame_statusbar_fields)):
			self.frame_statusbar.SetStatusText(frame_statusbar_fields[i], i)
		# end wxGlade

	def __do_layout(self):
		# begin wxGlade: MyFrame.__do_layout
		sizer_1 = wx.BoxSizer(wx.VERTICAL)
		sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_5 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Log"), wx.HORIZONTAL)
		sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
		self.sizer_sites = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Sites"), wx.VERTICAL)
		sizer_3 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, "Options"), wx.VERTICAL)
		sizer_3.Add(self.checkbox_verbose, 0, 0, 0)
		sizer_3.Add(self.checkbox_dry_run, 0, 0, 0)
		sizer_2.Add(sizer_3, 1, wx.ALL | wx.EXPAND, 8)
		self.sizer_sites.Add(self.checkbox_all_sites, 0, 0, 0)
		self.sizer_sites.Add(self.panel_site_list, 1, wx.EXPAND, 0)
		sizer_2.Add(self.sizer_sites, 1, wx.ALL | wx.EXPAND, 8)
		sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
		sizer_1.Add(self.radio_box_ops_copy_copy, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		sizer_5.Add(self.text_ctrl_log, 1, wx.EXPAND, 0)
		sizer_1.Add(sizer_5, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
		sizer_7.Add(self.button_start, 0, wx.ALIGN_CENTER | wx.RIGHT, 10)
		sizer_7.Add(self.button_stop, 0, wx.LEFT, 10)
		sizer_1.Add(sizer_7, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)
		self.SetSizer(sizer_1)
		self.Layout()
		# end wxGlade

	def on_all_sites(self, event):  # wxGlade: MyFrame.<event_handler>
		is_all = event.GetEventObject().IsChecked()
		for cbox in self.get_site_checkboxes():
			cbox.SetValue(is_all)
		self.set_button_states()

	def on_sites_checkbox(self, event):
		self.checkbox_all_sites.SetValue(False)
		self.set_button_states()
		if event.GetEventObject().IsChecked():
			self.set_status('')

	def get_site_checkboxes(self):
		cboxes = []
		for ctrl in self.GetChildren():
			if hasattr(ctrl, "site_name"):
				cboxes.append(ctrl)
		return cboxes
	
# end of class MyFrame

class MyApp(wx.App):
	def OnInit(self):
		self.frame = MyFrame(None, wx.ID_ANY, "")
		self.SetTopWindow(self.frame)
		self.frame.Show()
		return True

# end of class MyApp

class RedirectText(object):
	def __init__(self, aWxTextCtrl, guiThreadId):
		self.out = aWxTextCtrl
		self.guiThreadId = guiThreadId

	def write(self, string):
		threadId = threading.current_thread().ident
		if self.guiThreadId == threadId:
			self.out.WriteText(string)
		else:
			wx.CallAfter(self.out.WriteText, string)

class OpThread(threading.Thread):
	def __init__(self, callback):
		super().__init__()
		self.callback = callback
		self.errorCount = 0
		self.stopping = False
		self.done = False

	def run(self):
 		# self.move_checker = movedem.MoveChecker(self.args.dir_old, self.args.dir_new, callback=self.callback, args=self.args)
		# if self.args.debug:
		# 	self.move_checker.logger.setLevel(logging.DEBUG)
		# self.move_checker.do_checks()

		self.done = True

	def stop(self):
		#self.move_checker.stop_processing()
		self.stopping = True

class OpsRadioBox(wx.RadioBox):
	def __init__(self, parent, wx_id):
		self.op_map = {}
		for clz in drupalsites.OperationClasses:
			self.op_map[clz.name] = clz
		self.choices = [*self.op_map.keys()]
		self.choices.sort()
		super().__init__(parent, wx_id, "Operations", choices=self.choices,
						majorDimension=len(self.choices), style=wx.RA_SPECIFY_ROWS)
		for i in range(len(self.choices)):
			self.SetItemToolTip(i, self.op_map[self.choices[i]].desc)
		default_sel = "local_updates"
		default_sel_idx = self.choices.index(default_sel)
		self.SetSelection(default_sel_idx)
if __name__ == "__main__":
	app = MyApp(0)
	app.MainLoop()
