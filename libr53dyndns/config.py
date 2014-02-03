
from ConfigParser import SafeConfigParser
import re

class DynConfig(SafeConfigParser):
    """
    Subclass of SafeConfigParser to define some convenience methods
    """
    reListSplit = re.compile('[\s,;]*')

    def getlist(self , section , key):
        val = self.get(section , key)
        return self.reListSplit.split(val)
