from setuptools import setup

APP = ['arkos-install/Installer.py']
DATA_FILES = ['arkOS Installer.applescript']
OPTIONS = {'argv_emulation': True, 'iconfile': 'icon.icns',
	'resources': ['arkos-install/images','arkos-install/translations'],  
	'includes': ['netifaces', 'sip', 'PyQt4']}

setup(
	name='arkos_install',
	version='0.3.1',
	author='Jacob Cook',
	author_email='jacob@citizenweb.is',
	packages=['arkos_install'],
	url='http://arkos.io/docs/getting-started',
	description='Installs the latest arkOS image to an SD card',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
