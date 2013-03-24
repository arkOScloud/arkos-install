#!/usr/bin/env python

########################################################################
##
##  arkOS Installer for Linux
##  Copyright (C) 2013 Jacob Cook
##  jacob@ark-os.org
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

import os
import subprocess

# Launch the main program with sudo privileges
if os.geteuid() != 0 and os.path.exists('/usr/bin/gksudo'):
	subprocess.call(["/usr/bin/gksudo", "-D arkOS Installer", "./main.py"])
elif os.geteuid() != 0 and os.path.exists('/usr/bin/kdesudo'):
	subprocess.call(["/usr/bin/kdesudo", "--comment 'arkOS Installer'", "./main.py"])
elif os.geteuid() != 0:
	message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "You do not have sufficient privileges to run this program. Please run this program with 'sudo' instead.")
	message.run()
else:
	subprocess.call("./main.py")