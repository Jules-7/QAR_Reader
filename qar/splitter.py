from qarReader_prod_v2 import QARReader
from compact_flash import CompactFlash


class Split(object):

    """ This class redirect either to QAR or Compact Flash class"""

    def __init__(self, path, flag):
        self.result = None
        if flag is "qar":
            qar = QARReader(path)
            self.result = qar
        elif flag is "cf":
            cf = CompactFlash(path)
            self.result = cf
