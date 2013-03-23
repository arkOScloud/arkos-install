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

import gtk
import os
import sys
import platform
import re
import urllib2
import md5
import threading
import time
import gobject

gtk.gdk.threads_init()

def checker():
    # Make sure the user has the privileges necessary to run
    if os.geteuid() != 0:
        print "You do not have sufficient privileges to run this program. Please run 'sudo ./Installer.py' instead.\n"
        sys.exit()

class Installer:
    def __init__(self):
        # Create window
        self.installer = gtk.Assistant()
        self.installer.set_default_size(640, 400)
        self.installer.set_title("arkOS Installer")
        self.installer.connect("cancel", self.quit_it)
        self.installer.connect("close", self.quit_it)

        # Initialize basic pages
        self.create_page0()
        self.create_page1()
        self.create_page2()
        self.create_page3()

        self.installer.show()

    def quit_it(self, installer):
        # Run this when the user cancels or exits at a sensitive time
        message = gtk.MessageDialog(self.installer, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, "Are you sure you want to quit? The installation is not complete and you will not be able to use your SD card.\n\nIf a disk write operation is in progress, this will not be able to stop that process.")
        response = message.run()
        message.destroy()
        if response == gtk.RESPONSE_YES:
            self.installer.destroy()
            gtk.main_quit()
            os._exit(os.EX_OK)
        else:
            return

    def md5sum(self, fname):
        # Returns an md5 hash for the file parameter
        f = file(fname, 'rb')
        m = md5.new()
        while True:
            d = f.read(8096)
            if not d:
                break
            m.update(d)
        f.close()
        return m.hexdigest()

    def comparemd5(self):
        # Creates an md5 hash for the package and compares it to authentic
        pack_md5 = self.md5sum('latest.tar.gz')
        file_md5 = open('latest.tar.gz.md5.txt')
        compare_md5 = file_md5.read().decode("utf-8")
        file_md5.close()
        if not pack_md5 in compare_md5:
            return 0
        else:
            return 1

    def pkg_check(self):
        # If package exists, check authenticity then skip download if necessary
        self.greeting.set_text("<b>Package found!</b> Checking authenticity...")
        self.greeting.set_use_markup(gtk.TRUE)
        if os.path.exists("latest.tar.gz"):
            if os.path.exists("latest.tar.gz.md5.txt"):
                result = self.comparemd5()
                if result == 0:
                    # the md5s were different. continue with download as is
                    pass
                else:
                    # the md5s were the same! skip the download.
                    self.download_override = True
            else:
                self.dlmd5 = urllib2.urlopen("https://uspx.ark-os.org/latest.tar.gz.md5.txt")
                md5File = open('latest.tar.gz.md5.txt', 'w')
                md5File.write(self.dlmd5.read())
                md5File.close()
                result = self.comparemd5()
                if result == 0:
                    # the md5s were different. gotta redownload the package
                    pass
                else:
                    # the md5s were the same! skip the download.
                    self.download_override = True
        elif os.path.exists("latest.tar.gz.md5.txt"):
            os.remove("latest.tar.gz.md5.txt")
        self.greeting.set_text("Welcome to the arkOS Installer! This program will guide you through installing the arkOS image to an SD card inserted into your computer.\n\nOnce you click Forward, your computer will start downloading the arkOS image from our servers in preparation for the install. Please make sure your computer is connected to the Internet before continuing.")

        
    def create_page0(self):
        # Create introduction page
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "arkOS Installer")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_INTRO)
        self.greeting = gtk.Label("Welcome to the arkOS Installer! This program will guide you through installing the arkOS image to an SD card inserted into your computer.\n\nOnce you click Forward, your computer will start downloading the arkOS image from our servers in preparation for the install. Please make sure your computer is connected to the Internet before continuing.")
        self.greeting.set_line_wrap(True)
        vbox.pack_start(self.greeting, True, True, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, True)

    def create_page1(self):
        # Create mirror chooser page
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "1 - Choose Mirror")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_CONTENT)
        self.download_override = False

        if self.download_override == True:
            label = gtk.Label("The installer found an apparently healthy image in this folder.\nIt will install this image instead of downloading another.")
        else:
            label = gtk.Label("Choose the download mirror closest to your location.")
            self.usa = gtk.RadioButton(None, "New York (United States)")
            self.eur = gtk.RadioButton(self.usa, "Amsterdam (Netherlands)")
            self.usa.connect("clicked", self.choose_mirror, "0")
            self.eur.connect("clicked", self.choose_mirror, "1")
            vbox.pack_end(self.eur, True, True, 0)
            vbox.pack_end(self.usa, True, True, 0)
        label.set_line_wrap(True)
        vbox.pack_start(label, True, True, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, True)

    def choose_mirror(self, element, choice):
        # Remember the chosen mirror
        if choice == "0":
            self.mirror = "New York (United States)"
            self.dlink = "https://uspx.ark-os.org"
        else:
            self.mirror = "Amsterdam (The Netherlands)"
            self.dlink = "https://eupx.ark-os.org"

        self.dllabel.set_text(self.mirror)
        self.linklabel.set_text(self.dlink)

    def poll_devices(self, element):
        # Pull up the list of connected disks
        self.devinput.clear()
        self.installer.set_page_complete(self.devicepage, False)
        num = 0
        for lines in os.popen('fdisk -l').readlines():
            if lines.startswith("/dev/"):
                continue
            if lines.find("/dev/") == -1:
                continue
            num = num + 1
            dev = lines.split()[1].rstrip(":")
            size = lines.split()[2]
            unit = lines.split()[3].rstrip(",")
            self.devstore = [num, dev, size, unit]
            self.devinput.append([self.devstore[0], self.devstore[1], self.devstore[2], self.devstore[3]])

    def create_page2(self):
        # Create the page for choosing a device
        self.devicepage = gtk.VBox()
        self.devicepage.set_border_width(5)
        self.installer.append_page(self.devicepage)
        self.installer.set_page_title(self.devicepage, "2 - Choose Device")
        self.installer.set_page_type(self.devicepage, gtk.ASSISTANT_PAGE_CONTENT)
        label = gtk.Label("Choose the appropriate device from the list below. Note that it is very important to choose the correct device! If you choose another one you may seriously damage your system.")
        label.set_line_wrap(True)

        # Create list of devices
        self.devinput = gtk.ListStore(int, str, str, str)
        self.treeView = gtk.TreeView(self.devinput)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("#", cell, text=0)
        column.set_sort_column_id(0)
        self.treeView.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Device", cell, text=1)
        column.set_min_width(400)
        column.set_sort_column_id(1)
        self.treeView.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Size", cell, text=2)
        column.set_min_width(100)
        column.set_sort_column_id(2)
        self.treeView.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Unit", cell, text=3)
        column.set_sort_column_id(3)
        self.treeView.append_column(column)

        self.poll_devices(self)
        self.chosenone = self.treeView.get_selection()
        button = gtk.Button("Refresh")
        button.connect("clicked", self.poll_devices)
        self.treeView.connect("cursor_changed", self.choose_device)

        # Make it scroll!
        self.devicepage.pack_start(label, True, True, 0)
        scrolledw = gtk.ScrolledWindow()
        scrolledw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolledw.add(self.treeView)
        self.devicepage.add(scrolledw)
        self.devicepage.pack_end(button, False, True, 0)
        self.installer.set_page_complete(self.devicepage, False)
        self.devicepage.show_all()

    def choose_device(self, element):
        # Remember the chosen device
        (model, iter) = self.chosenone.get_selected()
        self.device = self.devinput.get_value(iter, 1)
        self.installer.set_page_complete(self.devicepage, True)
        self.devlabel.set_text(self.device)

    def create_page3(self):
        # Create the page showing the summary of chosen options
        self.summary = gtk.VBox()
        self.summary.set_border_width(5)
        self.mirror = "New York (United States)"
        self.dlink = "https://uspx.ark-os.org"
        self.device = "null"
        self.installer.append_page(self.summary)
        self.installer.set_page_title(self.summary, "3 - Confirm")
        self.installer.set_page_type(self.summary, gtk.ASSISTANT_PAGE_CONTENT)
        self.confirmlabel = gtk.Label("Please confirm the details below. Once you click Start, the download will begin, then the selected device will be erased and data will be overwritten.\n\n<b>NOTE that there is no way to halt the writing process once it begins.</b>")
        self.confirmlabel.set_use_markup(gtk.TRUE)
        self.confirmlabel.set_line_wrap(True)
        self.summary.pack_start(self.confirmlabel, True, True, 0)

        table = gtk.Table(3, 2, True)
        self.summary.add(table)

        if self.download_override == True:
            down = gtk.Label("File Source: ")
            table.attach(down, 0, 1, 0, 1)
            self.dllabel = gtk.Label("latest.tar.gz")
            table.attach(self.dllabel, 1, 2, 0, 1)

        else:
            down = gtk.Label("Download Mirror: ")
            table.attach(down, 0, 1, 0, 1)
            self.dllabel = gtk.Label(self.mirror)
            table.attach(self.dllabel, 1, 2, 0, 1)

            downlink = gtk.Label("Mirror Address: ")
            table.attach(downlink, 0, 1, 1, 2)
            self.linklabel = gtk.Label(self.dlink)
            table.attach(self.linklabel, 1, 2, 1, 2)

        dev = gtk.Label("Device: ")
        table.attach(dev, 0, 1, 2, 3)
        self.devlabel = gtk.Label(self.device)
        table.attach(self.devlabel, 1, 2, 2, 3)

        self.startbutton = gtk.Button("Start!")
        self.startbutton.connect("clicked", self.install_handler)
        self.summary.pack_end(self.startbutton, False, True, 0)

        self.summary.show_all()
        self.installer.set_page_complete(self.summary, False)

    def create_page4(self):
        # Create the page that actually does all the work
        self.installpage = gtk.VBox()
        self.installpage.set_border_width(5)
        self.installer.append_page(self.installpage)
        self.installer.set_page_title(self.installpage, "Installing arkOS")
        self.installer.set_page_type(self.installpage, gtk.ASSISTANT_PAGE_CONTENT)
        self.installer.commit()
        self.download_label = gtk.Label(" ")
        self.imgwriter_label = gtk.Label(" ")
        self.installpage.pack_start(self.download_label, True, True, 0)
        self.installpage.pack_start(self.imgwriter_label, True, True, 0)
        self.progressbar = gtk.ProgressBar()
        self.installpage.pack_start(self.progressbar, False, False, 0)
        self.installpage.show_all()
        self.installer.set_page_complete(self.installpage, False)

    def install_handler(self, element):
        # Redo the Summary page to give install info, and switch pages.
        self.installer.set_page_complete(self.summary, True)
        self.startbutton.hide()
        self.confirmlabel.set_text("The installer is in progress. Here are the settings you chose to use. Pass to the next page to see the install progress, or click the 'X' in the upper right-hand corner to cancel.")
        self.create_page4()
        self.installer.set_current_page(4)

        # Run the download and image writer functions, then go to the final page
        if self.download_override == True:
            self.download_label.set_text("File found: latest.tar.gz")
            self.download_label.set_use_markup(gtk.TRUE)
            self.download_label.set_line_wrap(True)
            md5error = self.comparemd5()
            if md5error == 0:
                installer.destroy()
                message = gtk.MessageDialog(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Installation failed: MD5 hashes are not the same. Remove the latest.tar.gz and latest.tar.gz.md5.txt files from this directory, then retry the install.")
                message.run()
            else:
                self.imgwriter_label.set_text("<b>Copying image to " + self.device + "...</b>\n(This will take a few minutes depending on SD card size.)")
                self.imgwriter_label.set_use_markup(gtk.TRUE)
                self.imgwriter_label.set_line_wrap(True)
                self.progressbar.set_fraction(0.0)
                self.write_it = ImgWriter(self.device)
                while self.write_it.isAlive():
                    self.progressbar.pulse()
                    while gtk.events_pending():
                        gtk.main_iteration()
                    time.sleep(0.1)
                self.imgwriter_label.set_text("Copying image to " + self.device + "... <b>DONE</b>")
                self.imgwriter_label.set_use_markup(gtk.TRUE)
                self.progressbar.set_fraction(1.0)
                self.create_page5()
                self.installer.set_current_page(5)
        else:
            self.download_label.set_text("<b>Downloading image from " + self.mirror + "...</b>")
            self.download_label.set_use_markup(gtk.TRUE)
            self.download_label.set_line_wrap(True)
            self.download_it = Downloader(self, self.dlink, 'latest.tar.gz.md5.txt', 'latest.tar.gz')
            self.download_label.set_text("Downloading image from " + self.mirror + "... <b>DONE</b>")
            self.download_label.set_use_markup(gtk.TRUE)
            md5error = self.comparemd5()
            if md5error == 0:
                installer.destroy()
                message = gtk.MessageDialog(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, "Installation failed: MD5 hashes are not the same. Remove the latest.tar.gz and latest.tar.gz.md5.txt files from this directory, then retry the install.")
                message.run()
            else:
                self.imgwriter_label.set_text("<b>Copying image to " + self.device + "...</b>\n(This will take a few minutes depending on SD card size.)")
                self.imgwriter_label.set_use_markup(gtk.TRUE)
                self.imgwriter_label.set_line_wrap(True)
                self.progressbar.set_fraction(0.0)
                self.progressbar.set_text(" ")
                self.write_it = ImgWriter(self.device)
                while self.write_it.isAlive():
                    self.progressbar.pulse()
                    while gtk.events_pending():
                        gtk.main_iteration()
                    time.sleep(0.1)
                self.imgwriter_label.set_text("Copying image to " + self.device + "... <b>DONE</b>")
                self.imgwriter_label.set_use_markup(gtk.TRUE)
                self.progressbar.set_fraction(1.0)
                self.create_page5()
                self.installer.set_current_page(5)

    def update_progress(self, bytes_so_far, chunk_size, total_size):
        # Looped function to update the progressbar for download
        percent = float(bytes_so_far) / total_size
        self.progressbar.set_fraction(percent)
        percent = round(percent*100, 2)
        self.progressbar.set_text("%0.2f of %0.2f MiB (%0.2f%%)" %
            (float(bytes_so_far)/1048576, float(total_size)/1048576, percent))
        return True

    def create_page5(self):
        # Create the final page with successful message
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "Complete")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_SUMMARY)
        self.installer.commit()
        label = gtk.Label("Congratulations! Your image has been written to the SD card successfully.\n\nInsert the SD card into your Raspberry Pi and connect it to your router. Continue setting up your server via a plugged-in keyboard and monitor.\n\nKeep an eye out for the arkOS Node Manager, coming soon!")
        label.set_line_wrap(True)
        vbox.pack_start(label, True, True, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, True)

class ImgWriter(threading.Thread):
    def __init__(self, device):
        threading.Thread.__init__(self)
        self.device = device
        self.start()

    def run(self):
        os.system("tar -xzOf latest.tar.gz | dd bs=1M of=" + self.device)
        os.system("blockdev --rereadpt " + self.device)

class Downloader(threading.Thread):
    # Handles the thread for download operations
    def __init__(self, delegate, mirror, *args):
        threading.Thread.__init__(self)
        self.delegate = delegate
        self.mirror = mirror + "/"
        self.filenames = []
        for filename in args:
            self.filenames.append(filename)
        self.start()

    def run(self):
        # Download the files and report their status
        for filename in self.filenames:
            print filename
            link = self.mirror + filename
            dl_file = urllib2.urlopen(link)
            io_file = open(filename, 'w')
            self.size_read(dl_file, io_file, 8192)
            io_file.close()

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
            gobject.idle_add(self.delegate.update_progress, bytes_so_far, chunk_size, total_size)
        return bytes_so_far

def main():
    checker()
    Installer()
    gtk.main()

if __name__ == '__main__':
    main()
