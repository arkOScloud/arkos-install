########################################################################
##
##  arkOS Installer for Mac OS X
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

tell application "Finder" to get folder of (path to me) as Unicode text
set workingDir to POSIX path of result
set py to "Installer.py "
set calldir to quoted form of workingDir & py
do shell script calldir with administrator privileges