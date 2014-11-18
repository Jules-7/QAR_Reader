from monstr import MonstrHeader
from boeing import Boeing
from bur_92 import Bur
from compactFlash import CompactFlash

ACFT_FDR_TYPES = {321: ["a320", "qar"],  # A320
                  322: ["a320", "cf"],
                  331: ["b747", "qar"],
                  341: ["an148", "bur92"],
                  351: ["an32", "testerU32"],
                  361: ["an26", "msrp12"]}
MONSTR_HEADER_TYPES = [321, 351, 361]
OWN_HEADER_TYPES = [322]
NO_HEADER_TYPES = [331, 341]


class Split(object):

    """ This class redirect to appropriate class
    depending on type of data source (QAR, CF, FDR) and aircraft type"""

    def __init__(self, path, flag):
        self.path = path
        self.flag = flag
        self.acft_fdr_type = "%s_%s" % (ACFT_FDR_TYPES[flag][0], ACFT_FDR_TYPES[flag][1])
        self.result = None
        self.define_file_opening()

    def define_file_opening(self):
        if self.flag in MONSTR_HEADER_TYPES:
            self.open_with_monstr_header(self.path, self.flag)
        elif self.flag in OWN_HEADER_TYPES:
            self.open_with_own_header(self.path, self.flag)
        elif self.flag in NO_HEADER_TYPES:
            self.open_with_no_header(self.path, self.flag)

    def open_with_monstr_header(self, path, acft_fdr_type):
        qar = MonstrHeader(path, acft_fdr_type)
        self.result = qar

    def open_with_own_header(self, path, flag):
        if flag == 322:
            self.result = CompactFlash(path)

    def open_with_no_header(self, path, flag):
        if flag == 331:  # boeing
            self.result = Boeing(path)
        elif flag == 341:  # bur92
            self.result = Bur(path)
