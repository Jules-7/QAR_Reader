from qarReader_prod_v2 import QARReader
from compact_flash import CompactFlash
from boeing import Boeing
from bur_92 import Bur


class Split(object):

    """ This class redirect to appropriate class
    depending on type of data source (QAR, CF, FDR) and aircraft type"""

    def __init__(self, path, flag):
        self.result = None
        if flag == "qar":
            qar = QARReader(path)
            self.result = qar
        elif flag is "a320_cf":
            cf = CompactFlash(path)
            self.result = cf
        elif flag is "b747_qar":
            boeing_check = Boeing(path)
            self.result = boeing_check
        elif flag is "an148_qar":
            bur = Bur(path)
            self.result = bur
        elif flag is "an32_qar":
            qar = QARReader(path)
            self.result = qar
        elif flag == "a320_qar":
            qar = QARReader(path, info="a320")
            self.result = qar
