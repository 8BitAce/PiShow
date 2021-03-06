import re
import sys


class Config:
    def __init__(self):
        self.dict = dict()

    def reload(self, filename):
        """
        Reads the configuration values from the config file.

        Parameters:
            filename: The name of the config file.
        Returns: n/a
        """
        try:
            config_file = open(filename, "r")
        except IOError:
            print "No config in current directory"
            sys.exit()

        config_text = config_file.readlines()
        config_file.close()

        for line in config_text:
            if re.match(r'^delay [0-9]+', line):
                delay = line.split()[1]
                self.dict["delay"] = int(delay)
            if re.match(r'^update_interval [0-9]+', line):
                update_interval = line.split()[1]
                self.dict["update_interval"] = int(update_interval)

    def delay(self):
        return self.dict["delay"] if "delay" in self.dict.keys() else 10

    def update_interval(self):
        return self.dict["update_interval"] \
            if "update_interval" in self.dict.keys() else 60
