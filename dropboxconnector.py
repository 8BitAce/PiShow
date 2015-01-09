import locale
import os
import sys

from dropbox import client, session

class DropboxConnector:
    TOKEN_FILE = "token_store.txt"

    def __init__(self, local_path, db_path):
        self.current_path = db_path
        self.local_directory = local_path

        self.api_client = None
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth1:'):
                #access_key, access_secret = serialized_token[len('oauth1:'):].split(':', 1)
                #sess = session.DropboxSession(self.app_key, self.app_secret)
                #sess.set_token(access_key, access_secret)
                #self.api_client = client.DropboxClient(sess)
                #print "[loaded OAuth 1 access token]"
                print "OAuth1 not supported."
                sys.exit()
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
        else:
            return None


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
