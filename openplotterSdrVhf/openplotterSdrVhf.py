#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2020 by Sailoog <https://github.com/openplotter/openplotter-sdr-vhf>
# Copyright (C) 2020 by e-sailing <https://github.com/e-sailing/openplotter-sdr-vhf>
#
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import wx, os, sys, webbrowser, subprocess, time, configparser
import wx.richtext as rt
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
from .version import version

class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin, ListCtrlAutoWidthMixin):
	def __init__(self, parent, height):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER, size=(650, height))
		CheckListCtrlMixin.__init__(self)
		ListCtrlAutoWidthMixin.__init__(self)

class MyFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-sdr-vhf',self.currentLanguage)

		wx.Frame.__init__(self, None, title='SDR VHF '+version, size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-sdr-vhf.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		self.editSerialButton = self.toolbar1.AddTool(103, _('Edit device serial number'), wx.Bitmap(self.currentdir+"/data/serial.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditSerialButton, self.editSerialButton)
		self.toolbar1.AddSeparator()
		self.refreshButton = self.toolbar1.AddTool(104, _('Refresh'), wx.Bitmap(self.currentdir+"/data/refresh.png"))
		self.Bind(wx.EVT_TOOL, self.OnRefreshButton, self.refreshButton)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.sdrApps = wx.Panel(self.notebook)
		self.systemd = wx.Panel(self.notebook)
		self.output = wx.Panel(self.notebook)
		self.notebook.AddPage(self.sdrApps, _('SDR apps'))
		self.notebook.AddPage(self.systemd, _('Processes'))
		self.notebook.AddPage(self.output, '')
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/sdr.png", wx.BITMAP_TYPE_PNG))
		img1 = self.il.Add(wx.Bitmap(self.currentdir+"/data/process.png", wx.BITMAP_TYPE_PNG))
		img2 = self.il.Add(wx.Bitmap(self.currentdir+"/data/output.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img1)
		self.notebook.SetPageImage(2, img2)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.appsDict = []

		app = {
		'name': 'DVB-T',
		'included': False,
		'show': 'vlc '+self.conf.home+'/.openplotter/dvb.xspf',
		'service': '',
		'edit': True,
		'install': self.platform.admin+' python3 '+self.currentdir+'/installDvbt.py',
		'uninstall': self.platform.admin+' python3 '+self.currentdir+'/unInstallDvbt.py',
		}
		self.appsDict.append(app)

		app = {
		'name': 'DAB',
		'included': False,
		'show': 'welle-io',
		'service': '',
		'edit': False,
		'install': self.platform.admin+' apt install -y welle.io',
		'uninstall': self.platform.admin+' apt autoremove -y welle.io',
		}
		self.appsDict.append(app)

		app = {
		'name': 'ADS-B',
		'included': False,
		'show': 'http://localhost/dump1090-fa/',
		'service': ['dump1090-fa','piaware'],
		'edit': True,
		'install': self.platform.admin+' python3 '+self.currentdir+'/installPiaware.py',
		'uninstall': self.platform.admin+' python3 '+self.currentdir+'/unInstallPiaware.py',
		}
		self.appsDict.append(app)

		app = {
		'name': 'GQRX',
		'included': False,
		'show': 'gqrx',
		'service': '',
		'edit': False,
		'install': self.platform.admin+' python3 '+self.currentdir+'/installGqrx.py',
		'uninstall': self.platform.admin+' python3 '+self.currentdir+'/unInstallGqrx.py',
		}
		self.appsDict.append(app)

		app = {
		'name': 'AIS',
		'included': True,
		'show': '',
		'service': ['openplotter-rtl_ais'],
		'edit': True,
		'install': '',
		'uninstall': '',
		}
		self.appsDict.append(app)

		self.pageSdrApps()
		self.pageSystemd()
		self.pageOutput()

		maxi = self.conf.get('GENERAL', 'maximize')
		if maxi == '1': self.Maximize()

		self.Centre()


	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0)) 

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:pass

	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/sdr-vhf/sdr-vhf_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event=0): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')

	def OnEditSerialButton(self,e):
		dlg = editSerial()
		res = dlg.ShowModal()
		if res == wx.OK:
			self.Close()
			self.Destroy()
			return
		dlg.Destroy()

################################################################################

	def pageSdrApps(self):
		self.listApps = wx.ListCtrl(self.sdrApps, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listApps.InsertColumn(0, _('Name'), width=135)
		self.listApps.InsertColumn(1, _('Status'), width=150)
		self.listApps.InsertColumn(2, _('Device index'), width=200)
		self.listApps.InsertColumn(3, _('Device serial'), width=200)
		self.listApps.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListAppsSelected)
		self.listApps.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListAppsDeselected)
		self.listApps.SetTextColour(wx.BLACK)

		self.toolbar2 = wx.ToolBar(self.sdrApps, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.showButton = self.toolbar2.AddTool(202, _('Show'), wx.Bitmap(self.currentdir+"/data/show.png"))
		self.Bind(wx.EVT_TOOL, self.OnShowButton, self.showButton)
		self.toolbar2.AddSeparator()
		self.editButton = self.toolbar2.AddTool(201, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditButton, self.editButton)
		self.toolbar2.AddSeparator()
		toolInstall= self.toolbar2.AddTool(203, _('Install'), wx.Bitmap(self.currentdir+"/data/install.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolInstall, toolInstall)
		toolUninstall= self.toolbar2.AddTool(205, _('Uninstall'), wx.Bitmap(self.currentdir+"/data/uninstall.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolUninstall, toolUninstall)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listApps, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar2, 0)
		self.sdrApps.SetSizer(sizer)

		self.OnRefreshButton()

	def onListAppsSelected(self, e):
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		self.onListAppsDeselected()
		apps = list(reversed(self.appsDict))
		if not apps[i]['included']:
			self.toolbar2.EnableTool(203,True)
			self.toolbar2.EnableTool(205,True)
		if self.listApps.GetItemBackgroundColour(i) != (200,200,200):
			if apps[i]['edit']:
				self.toolbar2.EnableTool(201,True)
			if apps[i]['show']: self.toolbar2.EnableTool(202,True)

	def onListAppsDeselected(self, event=0):
		self.toolbar2.EnableTool(202,False)
		self.toolbar2.EnableTool(203,False)
		self.toolbar2.EnableTool(205,False)
		self.toolbar2.EnableTool(201,False)

	def OnRefreshButton(self, event=0):
		from rtlsdr import RtlSdr
		serial_numbers = RtlSdr.get_device_serial_addresses()
		self.listApps.DeleteAllItems()
		for i in self.appsDict:
			item = self.listApps.InsertItem(0, i['name'])
			if i['name'] == 'AIS': 
				self.listApps.SetItem(item, 1, _('installed'))
				sdraisdeviceindex = self.conf.get('SDR-VHF', 'sdraisdeviceindex')
				if sdraisdeviceindex:
					self.listApps.SetItem(item, 2, sdraisdeviceindex)
					for ii in serial_numbers:
						if sdraisdeviceindex == str(RtlSdr.get_device_index_by_serial(ii)):
							self.listApps.SetItem(item, 3, ii)
			elif i['name'] == 'GQRX':
				if not os.path.isdir(self.conf.home+'/.config/gqrx'):
					self.listApps.SetItem(item, 1, _('not installed'))
					self.listApps.SetItemBackgroundColour(item,(200,200,200))
				else:
					self.listApps.SetItem(item, 1, _('installed'))
					try:
						device = ''
						gqrx_conf = configparser.ConfigParser()
						gqrx_conf.read(self.conf.home+'/.config/gqrx/default.conf')
						inputDevice = gqrx_conf.get('input', 'device')
						inputDevice = inputDevice.replace('"','')
						inputDevice = inputDevice.split('=')
						if inputDevice[0] == 'rtl': device = inputDevice[1]
						if device:
							self.listApps.SetItem(item, 2, device)
							for ii in serial_numbers:
								if device == str(RtlSdr.get_device_index_by_serial(ii)):
									self.listApps.SetItem(item, 3, ii)
					except Exception as e: print('error getting gqrx settings: '+str(e))
			elif i['name'] == 'ADS-B':
				if not self.platform.isInstalled('piaware'):
					self.listApps.SetItem(item, 1, _('not installed'))
					self.listApps.SetItemBackgroundColour(item,(200,200,200))
				else:
					self.listApps.SetItem(item, 1, _('installed'))
			elif i['name'] == 'DAB':
				if not self.platform.isInstalled('welle.io'):
					self.listApps.SetItem(item, 1, _('not installed'))
					self.listApps.SetItemBackgroundColour(item,(200,200,200))
				else:
					self.listApps.SetItem(item, 1, _('installed'))
					self.listApps.SetItem(item, 2, _('First available'))
			elif i['name'] == 'DVB-T':
				if not self.platform.isInstalled('w-scan'):
					self.listApps.SetItem(item, 1, _('not installed'))
					self.listApps.SetItemBackgroundColour(item,(200,200,200))
				else:
					self.listApps.SetItem(item, 1, _('installed'))
					self.listApps.SetItem(item, 2, _('First available'))
		'''
		listCount = range(self.listApps.GetItemCount())
		for i in listCount:
			index = self.listApps.GetItemText(i, 2)
			if index:
				for ii in listCount:
					if self.listApps.GetItemText(ii, 2) == index and i != ii:
						if self.listApps.GetItemText(i, 0) == 'AIS' or self.listApps.GetItemText(ii, 0) == 'AIS':
							command = 'systemctl show openplotter-rtl_ais --no-page'
							output = subprocess.check_output(command.split(),universal_newlines=True)
							if 'SubState=running' in output: self.listApps.SetItemBackgroundColour(i,(255,0,0))
						else:
							self.listApps.SetItemBackgroundColour(i,(255,0,0))
		'''
		self.onListAppsDeselected()
		try: self.set_listSystemd()
		except: pass

	def OnToolInstall(self, e):
		index = self.listApps.GetFirstSelected()
		if index == -1: return
		apps = list(reversed(self.appsDict))
		name = apps[index]['name']
		command = apps[index]['install']
		if command:
			msg = _('Are you sure you want to install ')+name+_(' and its dependencies?')
			dlg = wx.MessageDialog(None, msg, _('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
			if dlg.ShowModal() == wx.ID_YES:
				self.logger.Clear()
				self.notebook.ChangeSelection(2)
				popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
				for line in popen.stdout:
					if not 'Warning' in line and not 'WARNING' in line:
						self.logger.WriteText(line)
						self.ShowStatusBarYELLOW(_('Installing SDR app, please wait... ')+line)
						self.logger.ShowPosition(self.logger.GetLastPosition())
				self.OnRefreshButton()
				self.notebook.ChangeSelection(0)
				if name == 'GQRX': subprocess.call(['pulseaudio', '--start'])
			dlg.Destroy()

	def OnToolUninstall(self, e):
		index = self.listApps.GetFirstSelected()
		if index == -1: return
		apps = list(reversed(self.appsDict))
		name = apps[index]['name']
		command = apps[index]['uninstall']
		if command:
			msg = _('Are you sure you want to uninstall ')+name+_(' and its dependencies?')
			dlg = wx.MessageDialog(None, msg, _('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
			if dlg.ShowModal() == wx.ID_YES:
				self.logger.Clear()
				self.notebook.ChangeSelection(2)
				popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
				for line in popen.stdout:
					if not 'Warning' in line and not 'WARNING' in line:
						self.logger.WriteText(line)
						self.ShowStatusBarYELLOW(_('Uninstalling SDR app, please wait... ')+line)
						self.logger.ShowPosition(self.logger.GetLastPosition())
				self.OnRefreshButton()
				self.notebook.ChangeSelection(0)
			dlg.Destroy()

	def OnEditButton(self, e):
		i = self.listApps.GetFirstSelected()
		if i == -1: return
		apps = list(reversed(self.appsDict))
		index = self.listApps.GetItemText(i, 2)
		serial = self.listApps.GetItemText(i, 3)
		self.ShowStatusBarYELLOW(_('Stopping all SDR processes'))
		subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'stopProcesses'])
		if apps[i]['name'] == 'AIS':
			dlg = editSdrAis(index,serial,self.conf)
			res = dlg.ShowModal()
			if res == wx.OK:
				self.conf.set('SDR-VHF', 'sdraisdeviceindex', str(dlg.sdraisdeviceindex))
				self.conf.set('SDR-VHF', 'sdraisppm', str(dlg.sdraisppm))
				self.conf.set('SDR-VHF', 'sdraisport', str(dlg.sdraisport))
				self.manageSKconnection(dlg.sdraisport)
			dlg.Destroy()
		if apps[i]['name'] == 'DVB-T':
			dlg = editDvbt()
			res = dlg.ShowModal()
			if res == wx.ID_OK:
				command = 'w_scan -ft -c '+dlg.code+' -L > '+self.conf.home+'/.openplotter/dvb.xspf'
				msg = _('Scanning channels, please wait... ')
				self.logger.Clear()
				self.notebook.ChangeSelection(2)
				popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
				for line in popen.stdout:
					try:
						if not 'Warning' in line and not 'WARNING' in line:
							self.logger.WriteText(line)
							self.ShowStatusBarYELLOW(msg+line)
							self.logger.ShowPosition(self.logger.GetLastPosition())
					except Exception as e: self.logger.WriteText(str(e))
			dlg.Destroy()
		self.ShowStatusBarYELLOW(_('Restarting SDR processes ...'))
		subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'restartProcesses'])
		time.sleep(1)
		self.ShowStatusBarYELLOW(_('Done'))
		self.OnRefreshButton()

	def manageSKconnection(self,port):
		if self.platform.skDir:
			from openplotterSignalkInstaller import editSettings
			skSettings = editSettings.EditSettings()
			ID = 'OpenPlotter SDR AIS'
			if 'pipedProviders' in skSettings.data:
				for i in skSettings.data['pipedProviders']:
					try:
						if ID in i['id']: 
							skSettings.removeConnection(i['id'])
						elif port:
							if i['pipeElements'][0]['options']['type']=='NMEA0183':
								if i['pipeElements'][0]['options']['subOptions']['type']=='udp':
									if i['pipeElements'][0]['options']['subOptions']['port']==str(port): 
										ID = i['id']
					except Exception as e: print(str(e))
			if ID == 'OpenPlotter SDR AIS':
				if port: skSettings.setNetworkConnection(ID, 'NMEA0183', 'UDP', 'localhost', str(port))

	def OnShowButton(self, e):
		index = self.listApps.GetFirstSelected()
		if index == -1: return
		apps = list(reversed(self.appsDict))
		show = apps[index]['show']
		if show:
			if 'http' in show:
				webbrowser.open(show, new=2)
			else:
				subprocess.Popen((show).split())

################################################################################

	def pageSystemd(self):
		self.started = False
		self.aStatusList = [_('inactive'),_('active')]
		self.bStatusList = [_('dead'),_('running')] 

		self.listSystemd = CheckListCtrl(self.systemd, 152)
		self.listSystemd.InsertColumn(0, _('Autostart'), width=90)
		self.listSystemd.InsertColumn(1, _('App'), width=90)
		self.listSystemd.InsertColumn(2, _('Process'), width=140)
		self.listSystemd.InsertColumn(3, _('Status'), width=120)
		self.listSystemd.InsertColumn(4, '  ', width=100)
		self.listSystemd.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListSystemdSelected)
		self.listSystemd.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListSystemdDeselected)
		self.listSystemd.SetTextColour(wx.BLACK)

		self.listSystemd.OnCheckItem = self.OnCheckItem

		self.toolbar3 = wx.ToolBar(self.systemd, style=wx.TB_TEXT | wx.TB_VERTICAL)
		start = self.toolbar3.AddTool(301, _('Start'), wx.Bitmap(self.currentdir+"/data/start.png"))
		self.Bind(wx.EVT_TOOL, self.onStart, start)
		stop = self.toolbar3.AddTool(302, _('Stop'), wx.Bitmap(self.currentdir+"/data/stop.png"))
		self.Bind(wx.EVT_TOOL, self.onStop, stop)
		restart = self.toolbar3.AddTool(303, _('Restart'), wx.Bitmap(self.currentdir+"/data/restart.png"))
		self.Bind(wx.EVT_TOOL, self.onRestart, restart)	

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.listSystemd, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar3, 0)

		self.systemd.SetSizer(sizer)

		self.set_listSystemd()
		self.started = True

	def onListSystemdSelected(self, e):
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		self.toolbar3.EnableTool(301,True)
		self.toolbar3.EnableTool(302,True)
		self.toolbar3.EnableTool(303,True)


	def onListSystemdDeselected(self, event=0):
		self.toolbar3.EnableTool(301,False)
		self.toolbar3.EnableTool(302,False)
		self.toolbar3.EnableTool(303,False)


	def set_listSystemd(self):
		self.process = []
		apps = list(reversed(self.appsDict))
		for i in apps:
			if i['service']:
				for ii in i['service']:
					if i['name'] == 'ADS-B':
						if ii == 'piaware':
							if self.platform.isInstalled('piaware'): self.process.append({'app':i['name'], 'service':ii})
						if ii == 'dump1090-fa':
							if self.platform.isInstalled('dump1090-fa'): self.process.append({'app':i['name'], 'service':ii})						
					else:
						self.process.append({'app':i['name'], 'service':ii})
		self.listSystemd.DeleteAllItems()
		index = 1
		for i in self.process:
			index = self.listSystemd.InsertItem(sys.maxsize, '')
			self.statusUpdate(i['service'],index,i['app'])
		self.onListSystemdDeselected()

	def statusUpdate(self, process, index, app): 
		command = 'systemctl show ' + process + ' --no-page'
		output = subprocess.check_output(command.split(),universal_newlines=True)
		if 'UnitFileState=enabled' in output: self.listSystemd.CheckItem(index)
		self.listSystemd.SetItem(index, 1, app)
		self.listSystemd.SetItem(index, 2, process)
		self.listSystemd.SetItem(index, 3, self.aStatusList[('ActiveState=active' in output)*1])
		self.listSystemd.SetItem(index, 4, self.bStatusList[('SubState=running' in output)*1])
						
	def onStart(self,e):
		index = self.listSystemd.GetFirstSelected()
		if index == -1: return
		self.ShowStatusBarYELLOW(_('Starting process...'))
		self.onKillProcesses()
		subprocess.call((self.platform.admin + ' systemctl start ' + self.process[index]['service']).split())
		time.sleep(1)
		self.OnRefreshButton()
		self.ShowStatusBarGREEN(_('Done'))

	def onStop(self,e):
		index = self.listSystemd.GetFirstSelected()
		if index == -1: return
		self.ShowStatusBarYELLOW(_('Stopping process...'))
		subprocess.call((self.platform.admin + ' systemctl stop ' + self.process[index]['service']).split())
		time.sleep(1)
		self.OnRefreshButton()
		self.ShowStatusBarGREEN(_('Done'))

	def onRestart(self,e):
		index = self.listSystemd.GetFirstSelected()
		if index == -1: return
		self.ShowStatusBarYELLOW(_('Restarting process...'))
		self.onKillProcesses()
		subprocess.call((self.platform.admin + ' systemctl restart ' + self.process[index]['service']).split())
		time.sleep(1)
		self.OnRefreshButton()
		self.ShowStatusBarGREEN(_('Done'))
		
	def OnCheckItem(self, index, flag):
		if not self.started: return
		if flag:
			subprocess.call((self.platform.admin + ' systemctl enable ' + self.process[index]['service']).split())
		else:
			subprocess.call((self.platform.admin + ' systemctl disable ' + self.process[index]['service']).split())

	def onKillProcesses(self):
		subprocess.call(['pkill', '-15', 'rtl_test'])
		subprocess.call(['pkill', '-15', 'kal'])
		subprocess.call(['pkill', '-15', 'rtl_eeprom'])
		subprocess.call(['pkill', '-15', 'gqrx'])
		time.sleep(1)

################################################################################

	def pageOutput(self):
		self.logger = rt.RichTextCtrl(self.output, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP|wx.LC_SORT_ASCENDING)
		self.logger.SetMargins((10,10))

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.logger, 1, wx.EXPAND, 0)
		self.output.SetSizer(sizer)

################################################################################

class editSdrAis(wx.Dialog):
	def __init__(self, deviceIndex, deviceSerial, conf):
		self.deviceIndex = deviceIndex
		self.deviceSerial = deviceSerial
		self.conf = conf
		self.currentdir = os.path.dirname(os.path.abspath(__file__))

		wx.Dialog.__init__(self, None, title=_('Editing SDR AIS'), size=(500,444))
		panel = wx.Panel(self)

		listDevLabel = wx.StaticBox(panel, label=_(' Detected SDR devices '))
		self.listDev = wx.ListCtrl(panel, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,100))
		self.listDev.InsertColumn(0, _('Index'), width=80)
		self.listDev.InsertColumn(1, _('Serial'), width=145)
		self.listDev.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListDevSelected)
		self.listDev.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListDevDeselected)
		self.listDev.SetTextColour(wx.BLACK)

		finalSettingsLabel = wx.StaticBox(panel, label=_(' Settings '))
		ppmLabel = wx.StaticText(panel, label='PPM')
		self.ppm = wx.TextCtrl(panel)
		portLabel = wx.StaticText(panel, label=_('Output UDP port'))
		self.port = wx.TextCtrl(panel)

		calibrationLabel = wx.StaticBox(panel, label=_(' Calibration '))
		self.button_test_gain = wx.Button(panel, label=_('Initial PPM'))
		self.Bind(wx.EVT_BUTTON, self.onTestDevice, self.button_test_gain)

		bands_label = wx.StaticText(panel, label=_('Band'))
		self.band = wx.ComboBox(panel, choices = ['GSM850', 'GSM-R', 'GSM900', 'EGSM', 'DCS', 'PCS'], style = wx.CB_READONLY)
		self.getChannel = wx.Button(panel, label =_('Get channel'))
		self.Bind(wx.EVT_BUTTON, self.onGetChannel, self.getChannel)

		channel_label = wx.StaticText(panel, label =_('Channel'))
		self.channel = wx.TextCtrl(panel)
		self.getPpm = wx.Button(panel, label=_('Get PPM'))
		self.Bind(wx.EVT_BUTTON, self.onGetPpm, self.getPpm)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)
		deleteBtn = wx.Button(panel, label=_('Delete'))
		deleteBtn.Bind(wx.EVT_BUTTON, self.OnDelete)
		okBtn = wx.Button(panel, wx.ID_OK)
		okBtn.Bind(wx.EVT_BUTTON, self.OnOk)

		listDevLabelBox = wx.StaticBoxSizer(listDevLabel, wx.VERTICAL)
		listDevLabelBox.Add(self.listDev, 1, wx.ALL | wx.EXPAND, 5)
		listDevLabelBox.AddSpacer(5)

		finalBox = wx.StaticBoxSizer(finalSettingsLabel, wx.VERTICAL)
		finalBox.Add(ppmLabel, 0, wx.LEFT | wx.UP, 10)
		finalBox.Add(self.ppm, 0, wx.LEFT | wx.UP, 10)
		finalBox.Add(portLabel, 0, wx.LEFT | wx.UP, 10)
		finalBox.Add(self.port, 0, wx.LEFT | wx.UP, 10)

		firstBox = wx.BoxSizer(wx.HORIZONTAL)
		firstBox.Add(listDevLabelBox, 1, wx.ALL | wx.EXPAND, 5)
		firstBox.Add(finalBox, 1, wx.ALL | wx.EXPAND, 5)

		testBox = wx.BoxSizer(wx.VERTICAL)
		testBox.Add(self.button_test_gain, 0, wx.ALL | wx.EXPAND, 5)
		testBox.AddStretchSpacer(1)

		bandBox = wx.BoxSizer(wx.VERTICAL)
		bandBox.Add(bands_label, 0, wx.ALL | wx.EXPAND, 5)
		bandBox.Add(self.band, 0, wx.ALL | wx.EXPAND, 5)
		bandBox.Add(self.getChannel, 0, wx.ALL | wx.EXPAND, 5)

		channelBox = wx.BoxSizer(wx.VERTICAL)
		channelBox.Add(channel_label, 0, wx.ALL | wx.EXPAND, 5)
		channelBox.Add(self.channel, 0, wx.ALL | wx.EXPAND, 5)
		channelBox.Add(self.getPpm, 0, wx.ALL | wx.EXPAND, 5)

		calibrationLabelBox = wx.StaticBoxSizer(calibrationLabel, wx.HORIZONTAL)
		calibrationLabelBox.Add(testBox, 1, wx.ALL | wx.EXPAND, 10)
		calibrationLabelBox.Add(bandBox, 1, wx.ALL | wx.EXPAND, 10)
		calibrationLabelBox.Add(channelBox, 1, wx.ALL | wx.EXPAND, 10)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(cancelBtn, 1, wx.ALL | wx.EXPAND, 5)
		hbox.Add(deleteBtn, 1, wx.ALL | wx.EXPAND, 5)
		hbox.Add(okBtn, 1, wx.ALL | wx.EXPAND, 5)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(firstBox, 1, wx.ALL | wx.EXPAND, 0)
		vbox.Add(calibrationLabelBox, 1, wx.ALL | wx.EXPAND, 5)
		vbox.Add(hbox, 0, wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.Centre()

		self.read()

	def read(self):
		from rtlsdr import RtlSdr
		self.onListDevDeselected()
		serial_numbers = RtlSdr.get_device_serial_addresses()
		for i in serial_numbers:
			device_index = RtlSdr.get_device_index_by_serial(i)
			item = self.listDev.InsertItem(0, str(device_index))
			self.listDev.SetItem(item, 1, str(i))
		if self.deviceIndex and self.deviceSerial:
			for i in range(self.listDev.GetItemCount()):
				if str(self.deviceIndex) == self.listDev.GetItemText(i, 0) and str(self.deviceSerial) == self.listDev.GetItemText(i, 1):
					self.listDev.Select(i)
					self.onListDevSelected()

		sdraisppm = self.conf.get('SDR-VHF', 'sdraisppm')
		if not sdraisppm: sdraisppm = '0'
		self.ppm.SetValue(sdraisppm)

		sdraisport = self.conf.get('SDR-VHF', 'sdraisport')
		if not sdraisport: sdraisport = '10110'
		self.port.SetValue(sdraisport)

	def onListDevSelected(self,e=0):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		self.button_test_gain.Enable()
		self.getChannel.Enable()
		self.getPpm.Enable()
		self.band.Enable()
		self.channel.Enable()

	def onListDevDeselected(self,e=0):
		self.button_test_gain.Disable()
		self.getChannel.Disable()
		self.getPpm.Disable()
		self.band.Disable()
		self.channel.Disable()

	def onKillProcesses(self):
		subprocess.call(['pkill', '-15', 'rtl_test'])
		subprocess.call(['pkill', '-15', 'kal'])
		subprocess.call(['pkill', '-15', 'rtl_eeprom'])
		subprocess.call(['pkill', '-15', 'gqrx'])
		time.sleep(1)

	def onTestDevice(self,e):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		self.onKillProcesses()
		subprocess.call(['x-terminal-emulator','-e', 'rtl_test', '-d', self.listDev.GetItemText(i, 0), '-p'])

	def onGetChannel(self,e):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		self.onKillProcesses()
		subprocess.call(['x-terminal-emulator', '-e', 'bash', self.currentdir+'/data/kal.sh', self.listDev.GetItemText(i, 0), 's', self.band.GetValue(), self.ppm.GetValue(), _('Take note of the channel with the highest power value and press Enter to close this window.')])

	def onGetPpm(self,e):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		self.onKillProcesses()
		subprocess.call(['x-terminal-emulator', '-e', 'bash', self.currentdir+'/data/kal.sh', self.listDev.GetItemText(i, 0), 'c', self.channel.GetValue(), self.ppm.GetValue(), _('Take note of the final ppm value rounded to the nearest whole number and press Enter to close this window.')])

	def OnOk(self,e):
		i = self.listDev.GetFirstSelected()
		if i == -1:
			wx.MessageBox(_('Please select a device.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		self.sdraisdeviceindex = self.listDev.GetItemText(i, 0)
		try:
			self.sdraisppm = int(self.ppm.GetValue())
		except:
			wx.MessageBox(_('PPM value must be a whole number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		try:
			self.sdraisport = int(self.port.GetValue())
		except:
			wx.MessageBox(_('UDP port value must be a whole number.'), _('Error'), wx.OK | wx.ICON_ERROR)
			return
		self.EndModal(wx.OK)

	def OnDelete(self,e):
		self.sdraisdeviceindex = ''
		self.sdraisppm = ''
		self.sdraisport = ''
		self.EndModal(wx.OK)

################################################################################

class editSerial(wx.Dialog):
	def __init__(self):
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.platform = platform.Platform()

		wx.Dialog.__init__(self, None, title=_('Editing devices serial number'), size=(400,300))
		panel = wx.Panel(self)

		detectedLabel = wx.StaticText(panel, label =_(' Detected SDR devices '))

		self.listDev = wx.ListCtrl(panel, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES, size=(-1,200))
		self.listDev.InsertColumn(0, _('Index'), width=80)
		self.listDev.InsertColumn(1, _('Serial'), width=300)
		self.listDev.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListDevSelected)
		self.listDev.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onListDevDeselected)
		self.listDev.SetTextColour(wx.BLACK)

		self.serial = wx.TextCtrl(panel)
		self.serial.SetMaxLength(8)
		self.setSerial = wx.Button(panel, label=_('Change serial'))
		self.Bind(wx.EVT_BUTTON, self.onSetSerial, self.setSerial)

		cancelBtn = wx.Button(panel, wx.ID_CANCEL)

		setSerialBox = wx.BoxSizer(wx.HORIZONTAL)
		setSerialBox.Add(self.setSerial, 0, wx.ALL | wx.EXPAND, 0)
		setSerialBox.Add(self.serial, 1, wx.LEFT | wx.EXPAND, 5)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(detectedLabel, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(self.listDev, 1, wx.ALL | wx.EXPAND, 5)
		vbox.Add(setSerialBox, 0, wx.ALL | wx.EXPAND, 5)
		vbox.AddStretchSpacer(1)
		vbox.Add(cancelBtn, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(vbox)
		self.Centre()

		self.read()

	def read(self):
		from rtlsdr import RtlSdr
		self.onListDevDeselected()
		serial_numbers = RtlSdr.get_device_serial_addresses()
		for i in serial_numbers:
			device_index = RtlSdr.get_device_index_by_serial(i)
			item = self.listDev.InsertItem(0, str(device_index))
			self.listDev.SetItem(item, 1, str(i))

	def onListDevSelected(self,e=0):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		self.serial.SetValue(self.listDev.GetItemText(i, 1))
		self.serial.Enable()
		self.setSerial.Enable()

	def onListDevDeselected(self,e=0):
		self.serial.Disable()
		self.setSerial.Disable()

	def onSetSerial(self,e):
		i = self.listDev.GetFirstSelected()
		if i == -1: return
		dlg = wx.MessageDialog(None, _('All programs and processes that use SDR devices will stop and you will need to manually restart them after changing the device serial number.\n\nAre you sure?'),
			_('Question'), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		if dlg.ShowModal() == wx.ID_YES:
			subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'stopProcesses'])
			subprocess.Popen(['x-terminal-emulator', '-e', 'bash', self.currentdir+'/data/rtl_eeprom.sh', self.listDev.GetItemText(i, 0), self.serial.GetValue(), _('Please replug the device for changes to take effect. Press Enter to close this window.')])
			self.EndModal(wx.OK)
		dlg.Destroy()

################################################################################

class editDvbt(wx.Dialog):
	def __init__(self):
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.platform = platform.Platform()

		wx.Dialog.__init__(self, None, title=_('Escanning DVB-T channels'), size=(370,120))
		panel = wx.Panel(self)

		codeLabel = wx.StaticText(panel, label =_('Country code'))
		self.countryCode = wx.TextCtrl(panel)

		countriesList = wx.Button(panel, label=_('Get list'))
		self.Bind(wx.EVT_BUTTON, self.onCountriesList, countriesList)

		scan = wx.Button(panel, label=_('Scan'))
		self.Bind(wx.EVT_BUTTON, self.onScan, scan)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(codeLabel, 1, wx.ALL | wx.EXPAND, 5)
		hbox.Add(self.countryCode, 1, wx.ALL | wx.EXPAND, 5)
		hbox.Add(countriesList, 1, wx.ALL | wx.EXPAND, 5)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 5)
		vbox.Add(scan, 0, wx.ALL | wx.EXPAND, 5)

		panel.SetSizer(vbox)
		self.Centre()

	def onScan(self,e):
		self.code = self.countryCode.GetValue()
		self.EndModal(wx.ID_OK)

	def onCountriesList(self,e):
		subprocess.call(['x-terminal-emulator', '-e', 'bash', self.currentdir+'/data/countries.sh'])

################################################################################

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'sdr_vhf'): 
			subprocess.Popen(['openplotterPostInstall', platform2.admin+' sdrVhfPostInstall'])
			return
	except: pass

	app = wx.App()
	MyFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
