
from configparser import ConfigParser
import re

class DynConfig(ConfigParser):
    """
    Subclass of SafeConfigParser to define some convenience methods
    """
    re_list_split = re.compile('[\s,;]+')

    def getlist(self, section, key):
        val = self.get(section, key)
        return self.re_list_split.split(val)
