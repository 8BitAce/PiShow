import locale
import os
import subprocess

from dropbox import client, session
from time import sleep

APP_KEY = ''
APP_SECRET = ''

DB_PATH = "Photos/Sample Album"
DELAY = 10

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
            pass # don't worry if it's not there

    def get_file_list(self, directory):
        resp = self.api_client.metadata(directory)

        if 'contents' in resp:
            files = []
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1] or 'ascii'
                files.append(('%s' % name).encode(encoding))
            return files

    def get_file(self, filename):
        to_file = open(os.path.expanduser("Images/" + filename), "wb")

        f, metadata = self.api_client.get_file_and_metadata(self.current_path + "/" + filename)
        to_file.write(f.read())

class Slideshow:
    def __init__(self, dbc):
        self.file_set = set([f for f in os.listdir("Images") if os.path.isfile(os.path.join("Images",f))])
        self.dbc = dbc
        self.directory = "Photos/Sample Album"

    def run_show(self, delay):
        self.update_files()
        child = subprocess.Popen(["feh", "-FY", "-D", str(delay), "Images"])
        while(True):
            if(self.update_files):
                child.kill()
                child = subprocess.Popen(["feh", "-FY", "-D", str(delay), "Images"])
            sleep(60)

    def update_files(self):
        """Returns True if fileset changed"""
        db_files = self.dbc.get_file_list(self.directory)
        new_files = set(db_files) - self.file_set
        old_files = self.file_set - set(db_files)
        if new_files != set() or old_files != set():
            self.file_set = db_files
            for filename in new_files:
                self.dbc.get_file(filename)
            for filename in old_files:
                os.remove("Images/" + filename)
            print "Fileset changed."
            print self.file_set
            return True
        return False

def main():
    dbc = DropboxConnector(APP_KEY, APP_SECRET)
    slideshow = Slideshow(dbc)
    slideshow.run_show(DELAY)

if __name__ == "__main__":
	main()
