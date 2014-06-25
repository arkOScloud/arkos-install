from setuptools import setup

setup(
	name='arkos_install',
	version='0.3.2',
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
