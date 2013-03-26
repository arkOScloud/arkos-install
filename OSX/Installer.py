#!/usr/bin/env python

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

import gtk
import os

from gobject import idle_add, threads_init
from md5 import new
from Queue import Queue
from re import compile, sub, search, group
from subprocess import Popen, PIPE, STDOUT
from sys import exit
from time import sleep
from threading import Thread
from urllib2 import urlopen, HTTPError

gtk.gdk.threads_init()


###################################################
##  Gatekeeping Functions
###################################################

def check_priv():
    # Make sure the user has the privileges necessary to run
    if os.geteuid() != 0:
        error_handler("You do not have sufficient privileges to run this program. Please run 'sudo ./Installer.py' from the Terminal instead.")

def error_handler(errormsg):
    # Throw up an error with the appropriate message and quit the application
    message = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, errormsg)
    message.run()
    os._exit(os.EX_CONFIG)


class Installer:

    ###################################################
    ##  Window Operation Functions
    ###################################################

    def __init__(self):
        # Create window
        self.installer = gtk.Assistant()
        self.installer.set_default_size(640, 400)
        self.installer.set_geometry_hints(self.installer, 640, 400)
        self.installer.set_title("arkOS Installer")
        self.installer.connect("cancel", self.quit_now)
        self.installer.connect("close", self.quit)

        self.queue = Queue()
        self.mirror_name = "New York (United States)"
        self.mirror_link = "https://uspx.ark-os.org"
        self.device = "null"

        # Initialize basic pages
        self.create_page0()
        self.create_page1()
        self.create_page2()
        self.create_page3()
        self.create_page4()
        self.create_page5()

        self.installer.show()

    def quit(self, installer):
        # Run this at the end of the process when the writing is done
        self.installer.destroy()
        gtk.main_quit()

    def quit_now(self, installer):
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


    ###################################################
    ##  Package and Hash Checking Functions
    ###################################################

    def md5sum(self):
        # Returns an md5 hash for the file parameter
        f = file('latest.tar.gz', 'rb')
        m = new()
        while True:
            d = f.read(8096)
            if not d:
                break
            m.update(d)
        f.close()
        pack_md5 = m.hexdigest()
        file_md5 = open('latest.tar.gz.md5.txt')
        compare_md5 = file_md5.read().decode("utf-8")
        file_md5.close()
        if not pack_md5 in compare_md5:
            return 0
        else:
            return 1

    def pkg_check(self, label):
        # If package exists, check authenticity then skip download if necessary
        if os.path.exists("latest.tar.gz"):
            label.set_text("<b>Package found in working directory!</b> Checking authenticity...")
            label.set_use_markup(gtk.TRUE)
            while gtk.events_pending():
                gtk.main_iteration()
            if os.path.exists("latest.tar.gz.md5.txt"):
                result = self.md5sum()
                if result == 0:
                    # the md5s were different. continue with download as is
                    label.set_text("Package found in working directory, but MD5 check failed. Redownloading...")
                    return 0
                else:
                    # the md5s were the same! skip the download.
                    label.set_text("Authentic package found in working directory. Skipping download...")
                    return 1
            else:
                dl_md5 = urlopen("https://uspx.ark-os.org/latest.tar.gz.md5.txt")
                md5_File = open('latest.tar.gz.md5.txt', 'w')
                md5_File.write(dl_md5.read())
                md5_File.close()
                result = self.md5sum()
                if result == 0:
                    # the md5s were different. gotta redownload the package
                    label.set_text("Package found in working directory, but MD5 check failed. Redownloading...")
                    return 0
                else:
                    # the md5s were the same! skip the download.
                    label.set_text("Authentic package found in working directory. Skipping download...")
                    return 1
        return 0


    ###################################################
    ##  Functions to Manage User Choices
    ###################################################  

    def choose_mirror(self, element, choice):
        # Remember the chosen mirror
        if choice == "0":
            self.mirror_name = "New York (United States)"
            self.mirror_link = "https://uspx.ark-os.org"
        else:
            self.mirror_name = "Amsterdam (The Netherlands)"
            self.mirror_link = "https://eupx.ark-os.org"

        self.dl_label.set_text(self.mirror_name)
        self.link_label.set_text(self.mirror_link)

    def poll_devices(self, element, page, list_store):
        # Pull up the list of connected disks
        list_store.clear()
        self.installer.set_page_complete(page, False)
        num = 0
        fdisk = Popen(['diskutil list'], stdout=PIPE)
        for lines in fdisk.stdout.readlines():
            if lines.startswith("0:"):
                continue
            if lines.find("0:") == -1:
                continue
            num = num + 1
            dev = lines.split()[1].rstrip(":")
            size = lines.split()[2]
            unit = lines.split()[3].rstrip(",")
            dev_store = [num, dev, size, unit]
            list_store.append([dev_store[0], dev_store[1], dev_store[2], dev_store[3]])

    def choose_device(self, element, page, tree_view, list_store):
        # Remember the chosen device
        (model, iter) = tree_view.get_selection().get_selected()
        self.device = list_store.get_value(iter, 1)
        self.installer.set_page_complete(page, True)
        self.device_label.set_text(self.device)

    def install_handler(self, element, page):
        # Redo the Summary page to give install info, and switch pages.
        self.installer.set_page_complete(page, True)
        self.installer.set_current_page(4)
        self.installer.commit()
        self.download_label.set_text("<b>Downloading image from " + self.mirror_name + "...</b>")
        self.download_label.set_use_markup(gtk.TRUE)
        override = self.pkg_check(self.download_label)

        if override == 0:
            # If no valid package was found, run the download and image writer threads
            download = Downloader(self.progressbar, self.queue, self.mirror_link, 'latest.tar.gz.md5.txt')
            download.start()
            while download.isAlive():
                while gtk.events_pending():
                    gtk.main_iteration()
            download_result = self.queue.get()
            if download_result != 200:
                error_handler("The file could not be downloaded. Please check your Internet connection. If the problem persists and your connection is fine, please contact the arkOS maintainers.\n\nHTTP Error " + str(download_result))
                return
            download = Downloader(self.progressbar, self.queue, self.mirror_link, 'latest.tar.gz')
            download.start()
            while download.isAlive():
                while gtk.events_pending():
                    gtk.main_iteration()
            download_result = self.queue.get()
            if download_result != 200:
                error_handler("The file could not be downloaded. Please check your Internet connection. If the problem persists and your connection is fine, please contact the arkOS maintainers.\n\nHTTP Error " + str(download_result))
                return
            self.download_label.set_text("Downloading image from " + self.mirror_name + "... <b>DONE</b>")
            self.download_label.set_use_markup(gtk.TRUE)

            md5error = self.md5sum()
            if md5error == 0:
                error_handler("Installation failed: MD5 hashes are not the same. Restart the installer and it will redownload the package. If this error persists, please contact the arkOS maintainers.")
                return

        self.imgwriter_label.set_text("<b>Copying image to " + self.device + "...</b>\n(This will take a few minutes depending on SD card size.)")
        self.imgwriter_label.set_use_markup(gtk.TRUE)
        self.progressbar.set_fraction(0.0)
        self.progressbar.set_text(" ")
        write = ImgWriter(self.device)
        while write.isAlive():
            self.progressbar.pulse()
            while gtk.events_pending():
                gtk.main_iteration()
            sleep(0.1)
        self.imgwriter_label.set_text("Copying image to " + self.device + "... <b>DONE</b>")
        self.imgwriter_label.set_use_markup(gtk.TRUE)
        self.installer.set_current_page(5)


    ###################################################
    ##  Page Content Functions
    ###################################################   

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
        label = gtk.Label("Choose the download mirror closest to your location.")
        usa = gtk.RadioButton(None, "New York (United States)")
        eur = gtk.RadioButton(usa, "Amsterdam (Netherlands)")
        usa.connect("clicked", self.choose_mirror, "0")
        eur.connect("clicked", self.choose_mirror, "1")
        vbox.pack_end(eur, True, True, 0)
        vbox.pack_end(usa, True, True, 0)
        label.set_line_wrap(True)
        vbox.pack_start(label, True, True, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, True)

    def create_page2(self):
        # Create the page for choosing a device
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "2 - Choose Device")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_CONTENT)
        label = gtk.Label("Choose the appropriate device from the list below. Note that it is very important to choose the correct device! If you choose another one you may seriously damage your system.")
        label.set_line_wrap(True)

        # Create list of devices
        list_store = gtk.ListStore(int, str, str, str)
        tree_view = gtk.TreeView(list_store)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("#", cell, text=0)
        column.set_sort_column_id(0)
        tree_view.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Device", cell, text=1)
        column.set_min_width(400)
        column.set_sort_column_id(1)
        tree_view.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Size", cell, text=2)
        column.set_min_width(100)
        column.set_sort_column_id(2)
        tree_view.append_column(column)
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Unit", cell, text=3)
        column.set_sort_column_id(3)
        tree_view.append_column(column)

        self.poll_devices(self, vbox, list_store)
        button = gtk.Button("Refresh")
        button.connect("clicked", self.poll_devices, vbox, list_store)
        tree_view.connect("cursor_changed", self.choose_device, vbox, tree_view, list_store)

        # Make it scroll!
        vbox.pack_start(label, True, True, 0)
        scrolledw = gtk.ScrolledWindow()
        scrolledw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        scrolledw.add(tree_view)
        vbox.add(scrolledw)
        vbox.pack_end(button, False, True, 0)
        self.installer.set_page_complete(vbox, False)
        vbox.show_all()

    def create_page3(self):
        # Create the page showing the summary of chosen options
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "3 - Confirm")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_CONTENT)
        label = gtk.Label("Please confirm the details below. Once you click Start, the download will begin, then the selected device will be erased and data will be overwritten.\n\n<b>NOTE that there is no way to halt the writing process once it begins.</b>")
        label.set_use_markup(gtk.TRUE)
        label.set_line_wrap(True)
        vbox.pack_start(label, True, True, 0)

        table = gtk.Table(3, 2, True)
        vbox.add(table)

        down = gtk.Label("Download Mirror: ")
        table.attach(down, 0, 1, 0, 1)
        self.dl_label = gtk.Label(self.mirror_name)
        table.attach(self.dl_label, 1, 2, 0, 1)
        downlink = gtk.Label("Mirror Address: ")
        table.attach(downlink, 0, 1, 1, 2)
        self.link_label = gtk.Label(self.mirror_link)
        table.attach(self.link_label, 1, 2, 1, 2)
        dev = gtk.Label("Device: ")
        table.attach(dev, 0, 1, 2, 3)
        self.device_label = gtk.Label(self.device)
        table.attach(self.device_label, 1, 2, 2, 3)

        self.startbutton = gtk.Button("Start!")
        self.startbutton.connect("clicked", self.install_handler, vbox)
        vbox.pack_end(self.startbutton, False, True, 0)

        vbox.show_all()
        self.installer.set_page_complete(vbox, False)

    def create_page4(self):
        # Create the page that actually does all the work
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "Installing arkOS")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_CONTENT)
        self.download_label = gtk.Label(" ")
        self.imgwriter_label = gtk.Label(" ")
        vbox.pack_start(self.download_label, True, True, 0)
        vbox.pack_start(self.imgwriter_label, True, True, 0)
        self.progressbar = gtk.ProgressBar()
        vbox.pack_start(self.progressbar, False, False, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, False)

    def create_page5(self):
        # Create the final page with successful message
        vbox = gtk.VBox()
        vbox.set_border_width(5)
        self.installer.append_page(vbox)
        self.installer.set_page_title(vbox, "Installation complete")
        self.installer.set_page_type(vbox, gtk.ASSISTANT_PAGE_SUMMARY)
        label = gtk.Label("Congratulations! Your image has been written to the SD card successfully.\n\nInsert the SD card into your Raspberry Pi and connect it to your router. Continue setting up your server via a plugged-in keyboard and monitor.\n\nKeep an eye out for the arkOS Node Manager, coming soon!")
        label.set_line_wrap(True)
        vbox.pack_start(label, True, True, 0)
        vbox.show_all()
        self.installer.set_page_complete(vbox, True)


###################################################
##  Threads for Long Processes
###################################################  

class Downloader(Thread):
    """

    Downloads the file passed to it.
    Args: progressbar - the widget in the main progress window
          queue - the message processing queue to pass HTTP errors
          mirror - the URL for the chosen mirror
          filename - the name of the file on the server to download

    """

    def __init__(self, progressbar, queue, mirror_link, filename):
        Thread.__init__(self)
        self.progressbar = progressbar
        self.queue = queue
        self.mirror_link = mirror_link + "/"
        self.filename = filename

    def run(self):
        # Download the files and report their status
        link = self.mirror_link + self.filename
        try:
            dl_file = urlopen(link)
        except HTTPError, e:
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
            self.update_progress(bytes_so_far, chunk_size, total_size)
        return bytes_so_far

    def update_progress(self, bytes_so_far, chunk_size, total_size):
        # Looped function to update the progressbar for download
        percent = float(bytes_so_far) / total_size
        idle_add(self.progressbar.set_fraction, percent)
        percent = round(percent*100, 2)
        idle_add(self.progressbar.set_text, "%0.2f of %0.2f MiB (%0.2f%%)" %
            (float(bytes_so_far)/1048576, float(total_size)/1048576, percent))
        return True

class ImgWriter(Thread):
    # Writes the downloaded image to disk
    def __init__(self, device):
        Thread.__init__(self)
        self.device = device
        self.start()

    def run(self):
        regex = compile('/dev/r?(self.device[0-9]+?)')
        try:
            disk = sub('r?disk', 'rdisk', regex.search(disk).group(0))
        except:
            error_handler("Malformed disk specification: ", disk)
            return
        unzip = Popen(['tar', 'xzOf', 'latest.tar.gz'], stdout=PIPE)
        dd = Popen(['dd', 'status=noxfer', 'bs=1m', 'of=' + disk], stdin=unzip.stdout, stderr=STDOUT)
        error = dd.communicate()[1]
        if error:
            error_handler("The disk writing process failed with the following error:\n\n" + error)


def main():
    check_priv()
    Installer()
    gtk.main()

if __name__ == '__main__':
    main()
