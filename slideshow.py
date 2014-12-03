import locale
import os
import re
import subprocess
import sys

from dropbox import client, session, rest
from time import sleep

class Slideshow:
    def __init__(self, dbc, local_dir, db_dir):
        self.dbc = dbc
        self.remote_directory = db_dir
        self.local_directory = local_dir
        self.file_set = set([f for f in os.listdir(self.local_directory) if os.path.isfile(os.path.join(self.local_directory,f))])
        self.config = Config()
        self.config_date = ""

    def run_show(self):
        self.update_files()
	self.check_config()
        child = subprocess.Popen(["feh", "-FY", "-D", str(self.config.delay()), self.local_directory])
        while(True):
            if(self.update_files()):
                child.kill()
                child = subprocess.Popen(["feh", "-FY", "-D", str(self.config.delay()), self.local_directory])
            if(self.check_config()):
                child.kill()
            sleep(self.config.update_interval())

    def update_files(self):
        """Returns True if fileset changed"""
        db_files = self.dbc.get_file_list(self.remote_directory)
        new_files = set(db_files) - self.file_set
        old_files = self.file_set - set(db_files)
        if new_files != set() or old_files != set():
            self.file_set = set(db_files)
            for filename in new_files:
                self.dbc.get_file(filename, self.local_directory)
            for filename in old_files:
                os.remove(self.local_directory + filename)
            print "Fileset changed:"
            print self.file_set
            return True
        return False

    def check_config(self):
        """Returns True if there is a new config"""
        try:
            config_metadata = self.dbc.get_metadata("config.txt")
        except rest.ErrorResponse:
            print "No config.txt in Dropbox directory. Exiting."
            sys.exit()
        if(config_metadata["modified"] != self.config_date):
            print "Config changed"
            self.config_date = config_metadata["modified"]
            self.dbc.get_file("config.txt", ".")
            self.config.reload(self.local_directory + "/" + "config.txt")
            return True