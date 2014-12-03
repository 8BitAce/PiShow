import locale
import os
import re
import subprocess
import sys

from dropbox import client, session, rest
from time import sleep

APP_KEY = ''
APP_SECRET = ''

class DropboxConnector:
    TOKEN_FILE = "token_store.txt"

    def __init__(self, app_key, app_secret, local_path, db_path):
        self.current_path = db_path
        self.local_directory = local_path

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
            print "Not authorized. Starting login process."
            self.do_login()

    def do_login(self):
        """log in to a Dropbox account"""
        key_file = None
        try:
	    key_file = open("app_key.txt", "r")
        except IOError:
            print "No app_key.txt. Exiting."
            sys.exit()
        keys = key_file.readlines()
        app_key = keys[0].strip()
        app_secret = keys[1].strip()
        flow = client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()
        sys.stdout.write("1. Go to: " + authorize_url + "\n")
        sys.stdout.write("2. Click \"Allow\" (you might have to log in first).\n")
        sys.stdout.write("3. Copy the authorization code.\n")
        code = raw_input("Enter the authorization code here: ").strip()

        try:
            access_token, user_id = flow.finish(code)
        except rest.ErrorResponse, e:
            self.stdout.write('Error: %s\n' % str(e))
            return

        with open(self.TOKEN_FILE, 'w') as f:
            f.write('oauth2:' + access_token)
        self.api_client = client.DropboxClient(access_token)

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
        to_file = None
        try:
            to_file = open(os.path.expanduser(self.local_directory + filename), "wb")
        except IOError:
            print self.local_directory + " is missing!"
            return

        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + filename)
        to_file.write(f.read())
        
    def get_metadata(self, filename):
        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + filename)
        return metadata

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
            if re.match(r'^delay [0-9+]', line):
                delay = line.split()[1]
                self.dict["delay"] = int(delay)

    def delay(self):
        return self.dict["delay"] if "delay" in self.dict.keys() else 10

    def update_interval(self):
        return self.dict["update_interval"] if "update_interval" in self.dict.keys() else 60

def main(argv):
    if(len(argv) < 3):
        print "Usage: pishow.py <local_image_directory> <dropbox_image_directory>"
        return
    local_directory = argv[1] + "/" if argv[1][-1] != "/" else argv[1]
    db_directory = argv[2] + "/" if argv[2][-1] != "/" else argv[2]
    dbc = DropboxConnector(APP_KEY, APP_SECRET, local_directory, db_directory)
    slideshow = Slideshow(dbc, local_directory, db_directory)
    slideshow.run_show()

if __name__ == "__main__":
	main(sys.argv)
