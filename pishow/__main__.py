from dropboxconnector import *
from slideshow import *


def main(argv):
    if len(argv) < 2:
        print "Usage: pishow <local_image_directory> " \
              "<dropbox_image_directory>"
        print "       pishow auth"
        return
    if argv[1] == "auth":
        DropboxConnector.do_login()
        return
    local_directory = argv[1] + "/" if argv[1][-1] != "/" else argv[1]
    db_directory = argv[2] + "/" if argv[2][-1] != "/" else argv[2]
    dbc = DropboxConnector(local_directory, db_directory)
    slideshow = Slideshow(dbc, local_directory, db_directory)
    slideshow.run_show()

if __name__ == "__main__":
    main(sys.argv)
