# arkOS Installer

This is the repository for the Windows, Mac OS X and Linux versions of the arkOS installer.

## Function

The arkOS Installer is an interactive graphical program allowing the user to choose several options of a customized installation experience. First, the user chooses the download mirror closest to their location. Then, they insert the SD card to their computer and choose it from a list of possible devices. Once these settings have been established, the program downloads an image of arkOS and checks it against the proper MD5 checksum, then installs it to an attached SD card, and provides the user with instruction on the next steps to get their Raspberry Pi up and running.

## How To Install

Check out the Downloads page at https://ark-os.org/downloads for stable installation packages. It is only advised to clone this repo if you plan on making contributions or bugfixes, which are totally welcome!

## To Add

* Clean up code and add better error handling
* Create Windows and Mac OS X versions (obviously)
* Automatically choose closest mirror via geoip check (?)
* Mount drive and set hostname, user/pass, network and ssh settings, etc