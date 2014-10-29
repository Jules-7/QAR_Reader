from qarReader_prod_v2 import QARReader
from compact_flash import CompactFlash
from boeing import Boeing
from bur_92 import Bur


class Split(object):

    """ This class redirect either to QARReader or to Compact Flash class """

    def __init__(self, path, flag):
        self.result = None
        if flag is "qar":
            qar = QARReader(path)
            self.result = qar
        elif flag is "cf":
            cf = CompactFlash(path)
            self.result = cf
        elif flag is "boeing_check":
            boeing_check = Boeing(path)
            self.result = boeing_check
        elif flag is "bur_92":
            bur = Bur(path)
            self.result = bur
