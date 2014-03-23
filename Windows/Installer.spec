# -*- mode: python -*-
import os

datafiles = []
for x in os.listdir(os.path.join(os.getcwd(), 'arkos_install/images')):
    f1 = os.path.join('arkos_install/images', x)
    if os.path.isfile(f1): # skip directories
        f2 = ('images/'+x, f1, 'DATA')
        datafiles.append(f2)
for x in os.listdir(os.path.join(os.getcwd(), 'arkos_install/translations')):
    f1 = os.path.join('arkos_install/translations', x)
    if os.path.isfile(f1): # skip directories
        f2 = ('translations/'+x, f1, 'DATA')
        datafiles.append(f2)

a = Analysis(['arkos_install\\Installer.py'],
             pathex=['C:\\Users\\Jake\\Documents\\installer'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
a.datas += datafiles
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='arkOS Installer.exe',
		  icon=os.path.join(os.getcwd(), 'arkos_install/images/icon.ico'),
          debug=False,
          strip=None,
          upx=True,
          console=0)
