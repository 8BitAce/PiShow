import locale
import os
import re
import sys
import time

from dropbox import client, rest


class DropboxConnector:
    TOKEN_FILE = "../token_store.txt"
    CURSOR_FILE = "../cursor.txt"
    APPKEY_FILE = "../app_key.txt"

    def __init__(self, local_path, db_path):
        """
        Parameters:
            local_path: The directory in which to store images on the Pi
            db_path: The remote directory located on the Dropbox account
        Returns: n/a
        """
        self.current_path = db_path
        self.local_directory = local_path

        self.api_client = None
        self.cursor = None
        # Try to read in the current cursor if it exists.
        try:
            curfile = open(self.CURSOR_FILE, "r")
            self.cursor = curfile.read()
            curfile.close()
        except IOError:
            pass
        try:
            serialized_token = open(self.TOKEN_FILE).read()
            if serialized_token.startswith('oauth1:'):
                print "OAuth1 not supported."
                sys.exit()
            elif serialized_token.startswith('oauth2:'):
                access_token = serialized_token[len('oauth2:'):]
                self.api_client = client.DropboxClient(access_token)
                print "[loaded OAuth 2 access token]"
            else:
                print "Malformed access token in %r." % (self.TOKEN_FILE,)
        except IOError:
            print "Not authorized. Use auth.sh to authenticate."

    @classmethod
    def do_login(cls):
        """
        Log in to a Dropbox account

        Parameters: n/a
        Returns: n/a
        """
        try:
            key_file = open(cls.APPKEY_FILE, "r")
        except IOError:
            print "No app_key.txt. Exiting."
            sys.exit()
        keys = key_file.readlines()
        app_key = keys[0].strip()
        app_secret = keys[1].strip()
        flow = client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)
        authorize_url = flow.start()
        sys.stdout.write("1. Go to: " + authorize_url + "\n")
        sys.stdout.write("2. Click \"Allow\" "
                         "(you might have to log in first).\n")
        sys.stdout.write("3. Copy the authorization code.\n")
        code = raw_input("Enter the authorization code here: ").strip()

        try:
            access_token, user_id = flow.finish(code)
        except rest.ErrorResponse, e:
            sys.stdout.write('Error: %s\n' % str(e))
            return

        with open(cls.TOKEN_FILE, 'w') as f:
            f.write('oauth2:' + access_token)
        # self.api_client = client.DropboxClient(access_token)

    def get_file_list(self, directory):
        """
        Gets a list of files in a Dropbox directory.

        Parameters:
            directory: The directory in which to get the filelist.
        Returns: A filelist if it is found, otherwise None.
        Raises: dropbox.rest.ErrorResponse
        """
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

    def get_file(self, filename):
        """
        Gets a file from the current Dropbox directory.

        Parameters:
            filename: The name of the desired file.
        Returns: The file
        Raises: dropbox.rest.ErrorResponse
        """
        try:
            to_file = open(os.path.expanduser(self.local_directory + filename),
                           "wb")
        except IOError:
            print self.local_directory + " is missing!"
            return

        f, metadata = self.api_client.get_file_and_metadata(
            self.current_path + "/" + filename)
        to_file.write(f.read())

    def get_metadata(self, filename):
        """
        Gets a file's metadata from the current Dropbox directory.

        Parameters:
            filename: The name of the desired file.
        Returns: The file's metadata
        Raises: dropbox.rest.ErrorResponse
        """
        f, metadata = self.api_client.get_file_and_metadata(
            self.current_path + "/" + filename)
        return metadata

    def poll(self, path):
        had_changes = False
        result = self.api_client.delta(self.cursor, path)
        self.cursor = result['cursor']
        # Write the cursor to a file to grab on next startup.
        with open(self.CURSOR_FILE, 'w') as mfile:
            mfile.write(self.cursor)

        if result['reset']:
            print 'RESET'

        if len(result['entries']) > 0:
            had_changes = True

        mpath = path
        for path, metadata in result['entries']:
            if path == mpath:
                continue
            filename = path.split("/")[-1]
            if metadata is not None:
                print '%s was created/updated' % path
                self.get_file(filename)
            else:
                print '%s was deleted' % path
                to_delete = [filename for filename
                             in os.listdir(self.local_directory)
                             if re.search(filename, filename, re.IGNORECASE)]
                if len(to_delete) >= 1:
                        os.remove(self.local_directory + "/" + to_delete[0])
                else:
                    print "Can't delete file. It doesn't exist!"

        # There are more results. Grab them too.
        while result['has_more']:
            result = self.api_client.delta(self.cursor, path)
            self.cursor = result['cursor']
            if result['reset']:
                print 'RESET'

            for path, metadata in result['entries']:
                filename = path.split("/")[-1]
                if metadata is not None:
                    print '%s was created/updated' % path
                    self.get_file(filename)
                else:
                    print '%s was deleted' % path
                    to_delete = [filename for filename
                                 in os.listdir(self.local_directory)
                                 if re.search(filename,
                                              filename, re.IGNORECASE)]
                    if len(to_delete) >= 1:
                        os.remove(self.local_directory + "/" + to_delete[0])
                    else:
                        print "Can't delete file. It doesn't exist!"

        # There were immediate changes. Return True to let the caller know.
        if had_changes:
            return True

        changes = False
        # poll until there are changes
        while not changes:
            result = self.api_client.longpoll_delta(self.cursor, 120)

            changes = result['changes']
            if not changes:
                print 'Timeout, polling again...'

            backoff = result['backoff'] if 'backoff' in result else None
            if backoff is not None:
                print 'Backoff requested. Sleeping for %d seconds...' % backoff
                time.sleep(backoff)
                print 'Resuming polling...'

        # There were changes, so recursively call poll to grab them
        # (and thus returning True)
        return self.poll(path)
