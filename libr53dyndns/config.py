
from configparser import SafeConfigParser
import re

class DynConfig(SafeConfigParser):
    """
    Subclass of SafeConfigParser to define some convenience methods
    """
    re_list_split = re.compile('[\s,;]+')

    def getlist(self, section, key):
        val = self.get(section, key)
        return self.re_list_split.split(val)
