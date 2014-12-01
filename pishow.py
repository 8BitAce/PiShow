import locale
import os
import subprocess
import sys

from dropbox import client, session
from time import sleep

APP_KEY = ''
APP_SECRET = ''

DB_PATH = "Photos/Sample Album"
DELAY = 5

class DropboxConnector:
    TOKEN_FILE = "token_store.txt"

    def __init__(self,app_key, app_secret):
        self.current_path = DB_PATH

        self.api_client = None
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth1:'):
                access_key, access_secret = serialized_token[len('oauth1:'):].split(':', 1)
                sess = session.DropboxSession(self.app_key, self.app_secret)
                sess.set_token(access_key, access_secret)
                self.api_client = client.DropboxClient(sess)
                print "[loaded OAuth 1 access token]"
            elif serialized_token.startswith('oauth2:'):
                access_token = serialized_token[len('oauth2:'):]
                self.api_client = client.DropboxClient(access_token)
                print "[loaded OAuth 2 access token]"
            else:
                print "Malformed access token in %r." % (self.TOKEN_FILE,)
        except IOError:
            print "Not authorized (no token_store.txt)."
            sys.exit()

    def get_file_list(self, directory):
        resp = self.api_client.metadata(directory)

        if 'contents' in resp:
            files = []
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1] or 'ascii'
                files.append(('%s' % name).encode(encoding))
            return files

    def get_file(self, filename, directory):
        to_file = open(os.path.expanduser(self.local_directory + filename), "wb")

        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + filename)
        to_file.write(f.read())

    def get_metadata(self, filename):
        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + filename)
        return metadata

class Slideshow:
    def __init__(self, dbc, local_dir):
        self.dbc = dbc
        self.remote_directory = DB_PATH
        self.local_directory = local_dir
        self.file_set = set([f for f in os.listdir(self.local_directory) if os.path.isfile(os.path.join(self.local_directory,f))])
        self.config = Config()
        self.config.reload()
        self.config_date = ""

    def run_show(self, delay):
        self.update_files()
        child = subprocess.Popen(["feh", "-FY", "-D", str(delay), self.local_directory])
        while(True):
            if(self.update_files()):
                child.kill()
                child = subprocess.Popen(["feh", "-FY", "-D", str(delay), self.local_directory])
            if(self.check_config()):
                child.kill()
            sleep(60)

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
        """Returns true if there is a new config"""
        config_metadata = self.dbc.get_metadata("config")
        if(config_metadata["modified"] != self.config_date):
            print "Config changed"
            self.config_date = config_metadata["modified"]
            self.dbc.get_file("config", ".")
            self.config.reload("config")
            return True

class Config:
    def __init__(self):
        self.dict = dict()

    def reload(self, filename):
        config_file = None
        try:
            config_file = open(filename, "r")
        except:
            print "No config in current directory"
            sys.exit()

        config_text = config_file.readlines()
        config_file.close()

        for line in config_text:
            if "delay" in line:
                delay = line.split()[1]
                self.dict["delay"] = int(delay)

    def delay(self):
        return self.dict["delay"] if "delay" in self.dict.keys() else 10

def main(argv):
    if(argv == None):
        print "Usage: pishow.py <local_image_directory>"
        return
    local_directory = argv + "/" if argv[-1] != "/" else argv
    dbc = DropboxConnector(APP_KEY, APP_SECRET)
    slideshow = Slideshow(dbc, local_directory)
    slideshow.run_show(DELAY)

if __name__ == "__main__":
	main(sys.argv[1])
