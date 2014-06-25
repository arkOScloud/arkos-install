#!/usr/bin/env python

########################################################################
##
##  arkOS Installer for Linux
##  Copyright (C) 2013-2014 Jacob Cook
##  jacob@citizenweb.is
##
##  Uses elements of Raspbmc Installer, (C) 2013 Sam Nazarko
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
########################################################################

import gettext
import json
import locale
import md5
import netifaces
import os
import re
import Queue
import socket
import ssl
import subprocess
import sys
import time
import urllib2
import xml.etree.ElementTree as ET

from PyQt4 import QtCore, QtGui


###################################################
##  Mirrors
################################################### 

def init_mirrorlist():
	global MIRRORS
	MIRRORS = {
		'nyus': {
			'name': _('New York, NY (United States)'),
			'status': 'official',
			'region': _('North America'),
			'url': 'https://nyus.mirror.arkos.io/'
		},
		'sfus': {
			'name': _('San Francisco, CA (United States)'),
			'status': 'official',
			'region': _('North America'),
			'url': 'https://sfus.mirror.arkos.io/'
		},
		'amnl': {
			'name': _('Amsterdam (The Netherlands)'),
			'status': 'official',
			'region': _('Europe'),
			'url': 'https://amnl.mirror.arkos.io/'
		},
		'sbfr': {
			'name': _('Strasbourg (France)'),
			'status': 'official',
			'region': _('Europe'),
			'url': 'https://sbfr.mirror.arkos.io/'
		},
		'frde': {
			'name': _('Frankfurt (Germany)'),
			'status': 'community',
			'region': _('Europe'),
			'url': 'http://frde.mirror.arkos.io/'
		},
		'pafr': {
			'name': _('Paris (France)'),
			'status': 'community',
			'region': _('Europe'),
			'url': 'http://pafr.mirror.arkos.io/'
		},
		'reis': {
			'name': _('Reykjavik (Iceland)'),
			'status': 'community',
			'region': _('Europe'),
			'url': 'http://reis.mirror.arkos.io/'
		},
		'nyus': {
			'name': _('Singapore'),
			'status': 'official',
			'region': _('Asia'),
			'url': 'https://sgsg.mirror.arkos.io/'
		},
		'tatw': {
			'name': _('Taipei (Taiwan)'),
			'status': 'community',
			'region': _('Asia/Pacific'),
			'url': 'http://tatw.mirror.arkos.io/'
		}
	}


###################################################
##  Internationalization
################################################### 

def init_internationalization():
	locale.setlocale(locale.LC_ALL, '')
	loc = locale.getlocale()
	if not loc[0]:
		translation = gettext.NullTranslations()
	else:
		filename = os.path.join(os.path.dirname(__file__), "translations/%s.mo" % loc[0][0:2])
		try:
			translation = gettext.GNUTranslations(open(filename, "rb"))
		except IOError:
			translation = gettext.NullTranslations()

	translation.install(True)

###################################################
##  Random Functions
###################################################

def error_handler(self, msg, close=True):
	# Throw up an error with the appropriate message and quit the application
	message = QtGui.QMessageBox.critical(self, _('Error'), msg, 
		QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
	if close is True:
		os._exit(os.EX_CONFIG)

def success_handler(self, msg, close=False):
	# Throw up a success message
	message = QtGui.QMessageBox.information(self, _('Success'), msg, 
		QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
	if close is True:
		os._exit(os.EX_CONFIG)

def centerOnScreen(window):
	resolution = QtGui.QDesktopWidget().screenGeometry()
	width = (resolution.width() / 2) - (window.frameSize().width() / 2)
	height = (resolution.height() / 2) - (window.frameSize().height() / 2)
	return width, height


###################################################
##  Welcome Dialog
################################################### 

class Assistant(QtGui.QWidget):
	def __init__(self):
		super(Assistant, self).__init__()

		# Create launcher window
		self.setFixedSize(375, 200)
		width, height = centerOnScreen(self)
		self.move(width, height)
		self.setWindowTitle(_('arkOS Installer'))
		self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/icon.png')))

		btn1 = QtGui.QPushButton(_('Install arkOS to an SD card'))
		btn1.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/install.png')))
		btn1.clicked.connect(self.installer)
		btn2 = QtGui.QPushButton(_('Search the network for arkOS devices'))
		btn2.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/search.png')))
		btn2.clicked.connect(self.finder)

		vbox = QtGui.QVBoxLayout()
		banner = QtGui.QLabel()
		banner.setPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), 'images/header.png')))
		banner.setAlignment(QtCore.Qt.AlignCenter)
		vbox.addWidget(banner)
		vbox.addWidget(btn1)
		vbox.addWidget(btn2)

		self.setLayout(vbox)
		self.check_priv()
		self.show()

	def check_priv(self):
		# Make sure the user has the privileges necessary to run
		if os.geteuid() != 0 and os.path.exists('/usr/bin/gksudo'):
			subprocess.Popen(["gksudo", "-D arkOS Installer", sys.executable, os.path.realpath(__file__)])
			os._exit(os.EX_CONFIG)
		elif os.geteuid() != 0 and os.path.exists('/usr/bin/kdesudo'):
			subprocess.Popen(["kdesudo", "--comment 'arkOS Installer'", sys.executable, os.path.realpath(__file__)])
			os._exit(os.EX_CONFIG)
		elif os.geteuid() != 0:
			error_handler(self, _('You do not have sufficient privileges '
				'to run this program. Please run sudo Installer.py instead.'))

	def installer(self):
		self.install = Installer()
		self.install.show()
		self.close()

	def finder(self):
		try:
			subprocess.check_call(['which', 'nmap'])
			self.find = Finder()
		except subprocess.CalledProcessError:
			error_handler(self, _('You need nmap installed in order to use this. '
				'Please install it from your distribution\'s software center or repositories.'), close=False)
		self.close()


###################################################
##  Network Browser
################################################### 

class AuthDialog(QtGui.QDialog):
	def __init__(self, parent, r, ip):
		super(AuthDialog, self).__init__(parent)
		self.setFixedSize(300, 150)
		width, height = centerOnScreen(self)
		self.move(width, height)
		self.setWindowTitle(_('Authenticate'))
		self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/icon.png')))

		vbox = QtGui.QVBoxLayout()
		label = QtGui.QLabel('<b>'+_('Give the username/password of a qualified user on the device')+'</b>')
		label.setWordWrap(True)
		table = QtGui.QGridLayout()
		ulabel = QtGui.QLabel(_('Username'))
		uline = QtGui.QLineEdit()
		plabel = QtGui.QLabel(_('Password'))
		pline = QtGui.QLineEdit()
		pline.setEchoMode(QtGui.QLineEdit.Password)
		table.addWidget(ulabel, 0, 0)
		table.addWidget(plabel, 1, 0)
		table.addWidget(uline, 0, 1)
		table.addWidget(pline, 1, 1)

		hbox = QtGui.QHBoxLayout()
		btn1 = QtGui.QPushButton(_('Cancel'))
		btn1.clicked.connect(self.close)
		btn1.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/cancel.png')))
		btn2 = QtGui.QPushButton(_('OK'))
		btn2.clicked.connect(lambda: self.send_sig(r, ip, uline, pline))
		btn2.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/ok.png')))
		btn2.setDefault(True)
		hbox.addStretch(1)
		hbox.addWidget(btn1)
		hbox.addWidget(btn2)

		vbox.addWidget(label)
		vbox.addLayout(table)
		vbox.addStretch(1)
		vbox.addLayout(hbox)

		self.setLayout(vbox)
		self.show()

	def send_sig(self, r, ip, user, passwd):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sslSocket = ssl.wrap_socket(s, 
				ssl_version=ssl.PROTOCOL_TLSv1)
			sslSocket.settimeout(10.0)
			sslSocket.connect((ip, 8765))
			sslSocket.write(json.dumps({
				'request': r,
				'user': str(user.text()),
				'pass': str(passwd.text()),
				}))
			sent = True
			rsp = json.loads(sslSocket.read())
			if 'ok' in rsp['response']:
				success_handler(self, _('Signal to %s sent successfully.') % r)
				self.close()
			else:
				error_handler(self, _('Authentification failed'), close=False)
			sslSocket.close()
		except Exception, e:
			if sent == True:
				success_handler(self, _('Signal to %s sent successfully, but I didn\'t get a response. '
					'Your command may or may not have completed.') % r)
				self.close()
			else:
				error_handler(self, _('There was an error processing your request.')+'\n\n'+str(e), close=False)
			sslSocket.close()
 

class Finder(QtGui.QWidget):
	def __init__(self):
		super(Finder, self).__init__()

		# Create finder window
		self.setFixedSize(640, 400)
		width, height = centerOnScreen(self)
		self.move(width, height)
		self.setWindowTitle(_('arkOS Network Finder'))
		self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/icon.png')))
		
		self.nodetype = None
		self.node = None

		vbox = QtGui.QVBoxLayout()
		self.tree_view = QtGui.QTreeWidget()
		self.tree_view.setHeaderLabels(['#', _('Name'), _('IP Address'), _('Genesis Status')])
		self.tree_view.setColumnWidth(0, 50)
		self.tree_view.setColumnWidth(1, 250)
		self.tree_view.setColumnWidth(2, 150)
		self.tree_view.setSortingEnabled(True)
		self.tree_view.sortByColumn(0, QtCore.Qt.AscendingOrder)
		self.tree_view.header().setMovable(False)

		hbox = QtGui.QHBoxLayout()
		btn1 = QtGui.QPushButton(_('Scan'))
		btn1.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/search.png')))
		btn1.clicked.connect(self.poll_nodes)
		hbox.addWidget(btn1)

		btn2 = QtGui.QPushButton(_('Shutdown'))
		btn2.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/shutdown.png')))
		btn2.clicked.connect(lambda: self.sig_node('shutdown'))
		hbox.addWidget(btn2)

		btn3 = QtGui.QPushButton(_('Restart'))
		btn3.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/restart.png')))
		btn3.clicked.connect(lambda: self.sig_node('restart'))
		hbox.addWidget(btn3)

		btn4 = QtGui.QPushButton(_('Reload Genesis'))
		btn4.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/reload.png')))
		btn4.clicked.connect(lambda: self.sig_node('reload'))
		hbox.addWidget(btn4)

		vbox.addWidget(self.tree_view)
		vbox.addLayout(hbox)
		self.setLayout(vbox)

		self.show()

	def poll_nodes(self):
		self.tree_view.clear()
		QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
		num = 0
		nodes = []

		# Step 1: determine local network IP range
		# 	If there is only one IP address and netmask, we will use that
		#	If not, use the first class C network range that comes up
		ranges1 = []
		ranges = []
		ifaces = netifaces.interfaces()
		if 'lo' in ifaces:
			ifaces.remove('lo')
		for iface in ifaces:
			try:
				addr = netifaces.ifaddresses(iface)[netifaces.AF_INET]
			except KeyError:
				continue
			for item in addr:
				ranges1.append((item['addr'], item['netmask']))

		for item in ranges1:
			addr = item[0].split('.')
			mask = item[1].split('.')
			addr = '.'.join([str(int(addr[x]) & int(mask[x])) 
				for x in range(0,4)])
			binary_str = ''
			for octet in mask:
				binary_str += bin(int(octet))[2:].zfill(8)
			mask = str(len(binary_str.rstrip('0')))
			addrrange = addr + '/' + mask
			ranges.append(addrrange)

		for item in ranges:
			if item.startswith('127'):
				ranges.remove(item)

		if len(ranges) == 0:
			error_handler(self, _('I couldn\'t find any networks. Please make sure you are connected to a network.'), close=False)
		elif len(ranges) == 1:
			addrrange = ''.join(ranges)
		else:
			for item in ranges:
				if item.startswith('192.168'):
					addrrange = item

		# Step 2: find all RPis on the network
		scan = subprocess.check_output(['nmap', '-oX', '-', '-sn', addrrange])
		hosts = ET.fromstring(scan)
		ips = []
		rpis = hosts.findall('.//address[@vendor="Raspberry Pi Foundation"]/..')
		for rpi in rpis:
			ips.append(rpi.find('.//address[@addrtype="ipv4"]').attrib['addr'])

		# Step 3: scan these RPis for Beacon instances
		for ip in ips:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			try:
				sslSocket = ssl.wrap_socket(s, 
					ssl_version=ssl.PROTOCOL_TLSv1)
				sslSocket.settimeout(10.0)
				sslSocket.connect((ip, 8765))
				sslSocket.write(json.dumps({
					'request': 'status'
					}))
				rsp = json.loads(sslSocket.read())
				if 'ok' in rsp['response']:
					nodes.append([num + 1, 
						rsp['name'], 
						ip, 
						rsp['status']
						])
				sslSocket.close()
			except:
				nodes.append([num + 1,
					_('Unknown (Raspberry Pi)'),
					ip,
					_('Unknown')
					])
				sslSocket.close()

		# Step 4: format the list of RPis and statuses into the GUI list
		for node in nodes:
			nodelist = QtGui.QTreeWidgetItem(self.tree_view)
			for item in enumerate(node):
				nodelist.setText(item[0], str(item[1]))
		QtGui.QApplication.restoreOverrideCursor()

	def sig_node(self, r):
		try:
			node = self.tree_view.currentItem().text(2)
		except AttributeError:
			error_handler(self, _('Please make a selection'), close=False)
			return

		if self.tree_view.currentItem().text(1).startsWith(_('Unknown')):
			error_handler(self, _('This feature can only be used on arkOS systems that have Beacon enabled'), close=False)
			return

		authdlg = AuthDialog(self, r, node)


###################################################
##  Installer Wizard - Pages
###################################################  

class IntroPage(QtGui.QWizardPage):
	def __init__(self, parent=None):
		super(IntroPage, self).__init__(parent)
		
		# Introduction page
		self.setTitle(_('Introduction'))
		label = QtGui.QLabel(_('Welcome to the arkOS Installer! This '
			'program will guide you through installing the arkOS image '
			'to an SD card inserted into your computer.')+'\n\n'
			+_('Once you click Forward, your computer will start downloading '
			'the arkOS image from our servers in preparation for the '
			'install. Please make sure your computer is connected to the '
			'Internet before continuing.'))
		label.setWordWrap(True)

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(label)

		self.setLayout(vbox)

	def nextId(self):
		return Installer.PageChooseMirror


class ChooseMirrorPage(QtGui.QWizardPage):
	def __init__(self, parent=None):
		super(ChooseMirrorPage, self).__init__(parent)
		self.parent = parent

		# Choose between the available mirrors
		self.setTitle(_('Choose Mirror'))
		label = QtGui.QLabel(_('Choose the download mirror closest to your '
			'location.'))
		label.setWordWrap(True)

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(label)

		btnnum = 0
		for x in sorted(MIRRORS):
			MIRRORS[x]['btn'] = QtGui.QRadioButton(MIRRORS[x]['name'])
			MIRRORS[x]['btn'].toggled.connect(self.set_selection)
			MIRRORS[x]['btn'].setChecked(True) if btnnum == 0 else None
			vbox.addWidget(MIRRORS[x]['btn'])
			btnnum = btnnum + 1

		self.setLayout(vbox)

	def nextId(self):
		return Installer.PageChooseDevice

	def set_selection(self):
		for x in MIRRORS:
			if MIRRORS[x]['btn'].isChecked():
				self.parent.mirror = x
				break


class ChooseDevicePage(QtGui.QWizardPage):
	def __init__(self, parent=None):
		super(ChooseDevicePage, self).__init__(parent)
		self.parent = parent

		# Select a device to write to
		self.setTitle(_('Choose Device'))
		label = QtGui.QLabel(_('Choose the appropriate device from the '
			'list below. Devices smaller than the minimum (2 GB) are not shown. '
			'Note that it is very important to choose the correct device! '
			'If you choose another one you may seriously damage your system.'))
		label.setWordWrap(True)

		self.tree_view = QtGui.QTreeWidget()
		self.tree_view.setHeaderLabels(['#', _('Device'), _('Size'), _('Unit')])
		self.tree_view.setColumnWidth(0, 50)
		self.tree_view.setColumnWidth(1, 375)
		self.tree_view.setColumnWidth(3, 50)
		self.tree_view.setSortingEnabled(True)
		self.tree_view.sortByColumn(0, QtCore.Qt.AscendingOrder)
		self.tree_view.header().setMovable(False)
		self.tree_view.itemSelectionChanged.connect(self.set_selection)

		btn1 = QtGui.QPushButton(_('Scan'))
		btn1.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/search.png')))
		btn1.clicked.connect(self.poll_devices)

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(label)
		vbox.addWidget(btn1)
		vbox.addWidget(self.tree_view)

		self.setLayout(vbox)
		self.poll_devices()

	def set_selection(self):
		try:
			self.parent.device = self.tree_view.currentItem().text(1)
		except AttributeError:
			self.parent.device = ''
		self.emit(QtCore.SIGNAL('completeChanged()'))

	def poll_devices(self):
		# Pull up the list of connected disks
		self.tree_view.clear()
		self.parent.device = ''
		self.emit(QtCore.SIGNAL('completeChanged()'))
		QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
		devices = []
		num = 0
		fdisk = subprocess.Popen(['fdisk', '-l'], 
			stdout=subprocess.PIPE).stdout.readlines()
		mounts = subprocess.Popen(['mount'], 
			stdout=subprocess.PIPE).stdout.readlines()

		uuids = {}
		try:
			for x in os.listdir('/dev/disk/by-uuid'):
				uuids[os.path.realpath(os.path.join('/dev/disk/by-uuid', x))] = x 
		except OSError:
			pass
		for lines in fdisk:
			if lines.startswith("/dev/") or lines.find("/dev/") == -1:
				continue

			devuuids = []
			dev = lines.split()[1].rstrip(":")
			for x in uuids:
				if x.startswith(dev):
					devuuids.append(uuids[x])
			r = re.compile("^\\s+([-,0-9. ]+)\\s+((?:[a-z][a-z]+))", re.IGNORECASE)
			m = r.match(lines.split(":")[1])
			try:
				size, unit = m.group(1), m.group(2)
			except AttributeError:
				continue

			if unit == 'GB' and float(size) <= 2.0:
				continue
			elif unit == 'MB' and float(size) <= 2048.0:
				continue

			present = False
			for thing in mounts:
				if dev in thing.split()[0] and thing.split()[2] == '/':
					present = True
					break
				for x in devuuids:
					if '/dev/disk/by-uuid/'+x in thing.split()[0] and thing.split()[2] == '/':
						present = True
						break
			
			if not present:
				num = num + 1
				devices.append([num, dev, size, unit])

		for device in devices:
			devlist = QtGui.QTreeWidgetItem(self.tree_view)
			for item in enumerate(device):
				devlist.setText(item[0], str(item[1]))
		QtGui.QApplication.restoreOverrideCursor()

	def nextId(self):
		return Installer.PageAction

	def isComplete(self):
		if self.parent.device != '':
			return True
		else:
			return False


class ActionPage(QtGui.QWizardPage):
	def __init__(self, parent=None):
		super(ActionPage, self).__init__(parent)
		self.parent = parent

		# Confirm the mirror and device choices before dl/write
		# Then carry out the installation
		self.setTitle(_('Confirm Details'))
		self.label = QtGui.QLabel(_('Please confirm the details below. Once you '
			'click Start, the download will begin, then the selected '
			'device will be erased and data will be overwritten.')+'<br><br>'
			+'<b>'+_('NOTE that there is no way to halt the writing process '
			'once it begins.')+'</b><br>')
		self.label.setWordWrap(True)
		self.mirlabel = QtGui.QLabel()
		self.devlabel = QtGui.QLabel()

		self.btn = QtGui.QPushButton(_('Start Download/Install'))
		self.btn.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/install.png')))
		self.btn.clicked.connect(self.install)

		self.vbox = QtGui.QVBoxLayout()
		self.vbox.addWidget(self.label)
		self.vbox.addWidget(self.mirlabel)
		self.vbox.addWidget(self.devlabel)
		self.vbox.addStretch(1)
		self.vbox.addWidget(self.btn)

		self.setLayout(self.vbox)

	def initializePage(self):
		self.mirlabel.setText('<b>'+_('Mirror')+':</b> %s' % MIRRORS[self.parent.mirror]['name'])
		self.devlabel.setText('<b>'+_('Device')+':</b> %s' % self.parent.device)

	def install(self):
		# Prepare the installation
		self.setTitle(_('Installing arkOS'))

		self.label.close()
		self.mirlabel.close()
		self.devlabel.close()
		self.btn.close()
		self.dllabel = QtGui.QLabel('<b>'+_('Downloading image from %s...') % MIRRORS[self.parent.mirror]['name'] + '</b>')
		self.imglabel = QtGui.QLabel()
		self.pblabel = QtGui.QLabel()
		self.progressbar = QtGui.QProgressBar()
		self.progressbar.setMinimum(0)
		self.progressbar.setMaximum(0)
		self.datalabel = QtGui.QLabel()
		self.vbox.addWidget(self.dllabel)
		self.vbox.addWidget(self.imglabel)
		self.vbox.addStretch(1)
		self.vbox.addWidget(self.progressbar)
		self.vbox.addWidget(self.datalabel)

		# Download package/MD5 if necessary
		override = self.pkg_check()
		if override == 0:
			# If no valid package was found, run the download and image writer threads
			self.download = Downloader(self.parent.queue, self.parent.mirror, 
				'latest-rpi.tar.gz.md5.txt')
			self.download.start()

			while self.download.isRunning():
				QtGui.QApplication.processEvents()
				time.sleep(0.1)

			download_result = self.parent.queue.get()
			if download_result != 200:
				error_handler(self, _('The file could not be downloaded. '
					'Please check your Internet connection. If the '
					'problem persists and your connection is fine, please '
					'contact the arkOS maintainers.')+'\n\n'+_('HTTP Error %s') % str(download_result))
				return

			self.progressbar.reset()
			self.progressbar.setMinimum(0)
			self.progressbar.setMaximum(100)

			self.download = Downloader(self.parent.queue, self.parent.mirror, 
				'latest-rpi.tar.gz')
			self.download.partDone.connect(self.updatebar)
			self.download.start()

			while self.download.isRunning():
				QtGui.QApplication.processEvents()
				time.sleep(0.1)

			download_result = self.parent.queue.get()
			if download_result != 200:
				error_handler(self, _('The file could not be downloaded. '
					'Please check your Internet connection. If the '
					'problem persists and your connection is fine, please '
					'contact the arkOS maintainers.')+'\n\n'+_('HTTP Error %s') % str(download_result))
				return

			self.dllabel.setText(_('Downloading image from %s...') % MIRRORS[self.parent.mirror]['name'] +' <b>'+_('DONE')+'</b>')

			md5error = self.md5sum()
			if md5error == 0:
				error_handler(self, _('Installation failed: MD5 hashes are '
					'not the same. Restart the installer and it will '
					'redownload the package. If this error persists, please '
					'contact the arkOS maintainers.'))
				return

		self.imglabel.setText('<b>'+_('Copying image to %s...') % self.parent.device +'</b><br>'
					+'('+_('This will take a few minutes depending on SD card size.')+')')
		self.imglabel.setWordWrap(True)
		self.progressbar.reset()
		self.progressbar.setMinimum(0)
		self.progressbar.setMaximum(0)

		self.write = ImgWriter(self.parent.queue, self.parent.device, 
			self.parent.path if self.parent.path else 'latest-rpi.tar.gz')
		self.datalabel.setText(_('Data write in progress.'))
		self.write.start()

		while self.write.isRunning():
			QtGui.QApplication.processEvents()

		write_result = self.parent.queue.get()
		if write_result != False:
			error_handler(self, _('The disk writing process failed with the '
							'following error:')+'\n\n'+write_result)
			return
		self.imglabel.setText(_('Copying image to %s...') % self.parent.device +' <b>'+_('DONE')+'</b>')
		self.parent.setPage(self.parent.PageConclusion, ConclusionPage(self.parent))
		self.parent.setOption(QtGui.QWizard.NoBackButtonOnLastPage, True)
		self.parent.next()

	def updatebar(self, val, got, total):
		self.progressbar.setValue(val)
		self.datalabel.setText(_('{:0.1f} of {:0.1f} MB - {}%').format(got, total, val))

	def pkg_check(self):
		# If package exists, check authenticity then skip download if necessary
		pkg_loc = 'latest-rpi.tar.gz'
		md5_loc = 'latest-rpi.tar.gz.md5.txt'
		if os.path.exists(pkg_loc):
			if os.path.islink(pkg_loc):
				pkg_loc = os.path.realpath(pkg_loc)
				self.parent.path = pkg_loc
			self.dllabel.setText(_('Package found in working directory! '
				'Checking authenticity...'))
			while QtGui.QApplication.hasPendingEvents():
				QtGui.QApplication.processEvents()
			if os.path.exists(md5_loc):
				if os.path.islink(md5_loc):
					md5_loc = os.path.realpath(md5_loc)
				result = self.md5sum(pkg_loc, md5_loc)
				if result == 0:
					# the md5s were different. continue with download as is
					self.dllabel.setText(_('Package found in working '
						'directory, but MD5 check failed. Redownloading...'))
					return 0
				else:
					# the md5s were the same! skip the download.
					self.dllabel.setText(_('Authentic package found in '
						'working directory. Skipping download...'))
					return 1
			else:
				dl_md5 = urllib2.urlopen(
					MIRRORS[self.parent.mirror]['url'] + 'latest-rpi.tar.gz.md5.txt'
				)
				md5_File = open('latest-rpi.tar.gz.md5.txt', 'w')
				md5_File.write(dl_md5.read())
				md5_File.close()
				result = self.md5sum(pkg_loc, 'latest-rpi.tar.gz.md5.txt')
				if result == 0:
					# the md5s were different. gotta redownload the package
					self.dllabel.setText(_('Package found in working '
						'directory, but MD5 check failed. Redownloading...'))
					return 0
				else:
					# the md5s were the same! skip the download.
					self.dllabel.setText(_('Authentic package found in '
						'working directory. Skipping download...'))
					return 1
		return 0

	def md5sum(self, pkg_loc, md5_loc):
		# Returns an md5 hash for the file parameter
		f = file(pkg_loc, 'rb')
		m = md5.new()
		while True:
			d = f.read(8096)
			if not d:
				break
			m.update(d)
		f.close()
		pack_md5 = m.hexdigest()
		file_md5 = open(md5_loc, 'r')
		compare_md5 = file_md5.read().decode("utf-8")
		file_md5.close()
		if not pack_md5 in compare_md5:
			return 0
		else:
			return 1

	def isComplete(self):
		return False


class ConclusionPage(QtGui.QWizardPage):
	def __init__(self, parent=None):
		super(ConclusionPage, self).__init__(parent)
		self.parent = parent

		# Show success message and setup instructions
		self.setTitle(_('Installation Complete'))
		label = QtGui.QLabel(_('Congratulations! Your image has been '
			'written to the SD card successfully.')+'<br><br>'+_('Insert the SD card '
			'into your Raspberry Pi and connect it to your router.')+'<br><br>'
			+_('After a minute or two, set up your server by opening your browser '
			'and connecting to Genesis at the following address:')
			+'<br><b>http://arkOS:8000</b><br>'
			+_('or use the Network Browser option in this Installer to '
			'find the IP address.')+'<br><br>'
			+_('Your initial Genesis login credentials are:')+'<br>'
			+_('Username:')+' <b>admin</b><br>'
			+_('Password:')+' <b>admin</b>')
		label.setWordWrap(True)
		self.box = QtGui.QCheckBox(_('Remove the downloaded files from your '
			'computer on exit'))

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(label)
		vbox.addWidget(self.box)

		self.setLayout(vbox)

	def initializePage(self):
		self.parent.cancelbtn.close()

	def validatePage(self):
		if self.box.isChecked():
			os.unlink('latest-rpi.tar.gz')
			os.unlink('latest-rpi.tar.gz.md5.txt')
		return True


###################################################
##  Installer Wizard - Base Class
###################################################  

class Installer(QtGui.QWizard):
	NUM_PAGES = 5

	(PageIntro, PageChooseMirror, PageChooseDevice, PageAction, 
		PageConclusion) = range(NUM_PAGES)

	mirror = 'nyus'
	device = ''
	queue = Queue.Queue()
	path = ''

	def __init__(self):
		super(Installer, self).__init__()

		# Create installer window
		self.setFixedSize(640, 400)
		width, height = centerOnScreen(self)
		self.move(width, height)
		self.setWindowTitle(_('arkOS Installer'))
		self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'images/icon.png')))

		self.setPage(self.PageIntro, IntroPage(self))
		self.setPage(self.PageChooseMirror, ChooseMirrorPage(self))
		self.setPage(self.PageChooseDevice, ChooseDevicePage(self))
		self.setPage(self.PageAction, ActionPage(self))

		self.cancelbtn = QtGui.QPushButton(_('Cancel'))
		self.cancelbtn.clicked.connect(self.quit_now)
		self.setButton(self.CustomButton1, self.cancelbtn)

		self.setOption(QtGui.QWizard.NoCancelButton, True)
		self.setOption(QtGui.QWizard.HaveCustomButton1, True)

		self.setStartId(self.PageIntro)

	def quit_now(self):
		# Run this when the user cancels or exits at a sensitive time
		msg = QtGui.QMessageBox.warning(self, _('Quit?'), 
			_('Are you sure you want to quit? The installation is not '
			'complete and you will not be able to use your SD card.')+'\n\n'
			+_('If a disk write operation is in progress, this will not be '
			'able to stop that process.'), QtGui.QMessageBox.Yes | 
			QtGui.QMessageBox.No, QtGui.QMessageBox.No)

		if msg == QtGui.QMessageBox.Yes:
			self.destroy()
			os._exit(os.EX_OK)
		else:
			return


###################################################
##  Installer Wizard - Threads for Long Processes
###################################################  

class Downloader(QtCore.QThread):
	"""

	Downloads the file passed to it.
	Args: queue - the message processing queue to pass HTTP errors
		  mirror - the ID of the chosen mirror
		  filename - the name of the file on the server to download

	"""

	partDone = QtCore.pyqtSignal((int, float, float))

	def __init__(self, queue, mirror, filename):
		super(Downloader, self).__init__()
		self.queue = queue
		self.mirror_link = MIRRORS[mirror]['url']
		self.filename = filename

	def run(self):
		# Download the files and report their status
		link = self.mirror_link + 'os/' + self.filename
		try:
			proxy = urllib2.ProxyHandler()
			opener = urllib2.build_opener(proxy)
			urllib2.install_opener(opener)
			dl_file = urllib2.urlopen(link)
		except urllib2.HTTPError, e:
			self.queue.put(e.code)
			return
		io_file = open(self.filename, 'w')
		self.size_read(dl_file, io_file, 8192)
		io_file.close()
		self.queue.put(200)

	def size_read(self, response, file, chunk_size):
		# Continually compare the amount downloaded with what is left to get
		# Then pass that data back to the main thread to update the progressbar
		total_size = response.info().getheader('Content-Length').strip()
		total_size = int(total_size)
		bytes_so_far = 0
		while 1:
			chunk = response.read(chunk_size)
			file.write(chunk)
			bytes_so_far += len(chunk)
			if not chunk:
				break
			percent = (float(bytes_so_far) / total_size) * 100
			ptxt = float(bytes_so_far) / 1048576
			ptot = float(total_size) / 1048576
			self.partDone.emit(percent, ptxt, ptot)
		return bytes_so_far


class ImgWriter(QtCore.QThread):
	# Writes the downloaded image to disk
	def __init__(self, queue, device, path):
		super(ImgWriter, self).__init__()
		self.device = device
		self.queue = queue
		self.path = path

	def run(self):
		# Write the image and refresh partition
		mounts = subprocess.Popen(['mount'], 
			stdout=subprocess.PIPE).stdout.readlines()
		for thing in mounts:
			if str(self.device) in thing.split()[0]:
				cmd = subprocess.Popen(['umount', str(thing).split()[0]]).wait()
		unzip = subprocess.Popen(['tar', 'xzOf', self.path], 
			stdout=subprocess.PIPE)
		dd = subprocess.Popen(
			['dd', 'status=noxfer', 'bs=1M', 'of=' + self.device], 
			stdin=unzip.stdout, stderr=subprocess.PIPE)
		error = dd.communicate()[1]
		if "error" in error:
			self.queue.put(error)
		else:
			self.queue.put(False)
			subprocess.Popen(['blockdev', '--rereadpt', self.device])


def main():
	init_internationalization()
	init_mirrorlist()
	app = QtGui.QApplication(sys.argv)
	asst = Assistant()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
