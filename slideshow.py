import os
import subprocess
import sys

from time import sleep

from config import *

class Slideshow:
    def __init__(self, dbc, local_dir, db_dir):
        """
        Parameters:
            dbc: The dropboxconnector to use.
            local_dir: The local directory that will hold the images.
            db_dir: The remote Dropbox directory containing the images.
        """
        self.dbc = dbc
        self.remote_directory = "/" + (db_dir[0:-1] if db_dir[-1] == "/" else db_dir)
        self.local_directory = local_dir
        self.file_set = set([f for f in os.listdir(self.local_directory) if os.path.isfile(os.path.join(self.local_directory,f))])
        self.config = Config()
        self.config_date = ""

    def run_show(self):
        """
        Run loop for slideshow.

        Parameters: n/a
        Returns: n/a
        """
        self.update_files()
        self.check_config()
        child = subprocess.Popen(["feh", "-FY", "-Sfilename", "-D", str(self.config.delay()), self.local_directory])
        while(True):
            if(self.dbc.poll(self.remote_directory)):
                child.kill()
                child = subprocess.Popen(["feh", "-FY", "-Sfilename", "-D", str(self.config.delay()), self.local_directory])

    def update_files(self):
        """
        Updates fileset from Dropbox if it has changed.
        Returns True if fileset changed.

        Parameters: n/a
        Returns: True if fileset has changed, otherwise False
        """
        try:
            db_files = self.dbc.get_file_list(self.remote_directory)
        except rest.ErrorResponse as e:
            print e.reason
        if db_files is None:
            print "Could not get remote file list."
            return False
        new_files = set(db_files) - self.file_set
        old_files = self.file_set - set(db_files)
        if new_files != set() or old_files != set():
            self.file_set = set(db_files)
            for filename in new_files:
                try:
                    self.dbc.get_file(filename)
                except rest.ErrorResponse as e:
                    print e.reason
            for filename in old_files:
                try:
                    os.remove(self.local_directory + "/" + filename)
                except:
                    pass
            print "Fileset changed:"
            print self.file_set
            return True
        return False

    def check_config(self):
        """
        Checks for a new config in Dropbox and downloads it.
        Returns True if there is a new config.

        Parameters: n/a
        Returns: True if there is a new config, otherwise False
        """
        try:
            config_metadata = self.dbc.get_metadata("config.txt")
        except rest.ErrorResponse:
            print "No config.txt in Dropbox directory. Exiting."
            sys.exit()
        if(config_metadata["modified"] != self.config_date):
            print "Config changed"
            self.config_date = config_metadata["modified"]
            try:
                self.dbc.get_file("config.txt")
            except rest.ErrorResponse as e:
                print e.reason
                return False
            self.config.reload(self.local_directory + "/" + "config.txt")
            return True
        return False
