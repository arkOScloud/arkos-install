from distutils.core import setup

setup(
	name='arkos_install',
	version='0.3',
	author='Jacob Cook',
	author_email='jacob@citizenweb.is',
	packages=['arkos_install'],
	package_data={'arkos_install': ['images/*']},
	scripts=['arkos-install'],
	url='http://arkos.io/docs/getting-started',
	description='Installs the latest arkOS image to an SD card',
	data_files=[
		('/usr/share/applications', ['arkos-install.desktop']),
		('/usr/share/icons/hicolor/16x16/apps', ['icons/16x16/arkos-install.png']),
		('/usr/share/icons/hicolor/22x22/apps', ['icons/22x22/arkos-install.png']),
		('/usr/share/icons/hicolor/32x32/apps', ['icons/32x32/arkos-install.png']),
		('/usr/share/icons/hicolor/48x48/apps', ['icons/48x48/arkos-install.png']),
		('/usr/share/icons/hicolor/64x64/apps', ['icons/64x64/arkos-install.png']),
		('/usr/share/icons/hicolor/128x128/apps', ['icons/128x128/arkos-install.png'])
	],
)