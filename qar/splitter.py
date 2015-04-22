from monstr import MonstrHeader
from boeing import Boeing737DFDR980, B747
from bur_92 import Bur
from compactFlash import CompactFlash
from source_data import QAR_TYPES, MONSTR_HEADER_TYPES
from source_data import OWN_HEADER_TYPES, NO_HEADER_TYPES


class Redirect(object):

    """ This class redirect to appropriate class
        depending on type of data source (QAR, CF, FDR) and aircraft type"""

    def __init__(self, path, flag, progress_bar):
        self.path = path
        self.flag = flag
        self.acft_fdr_type = "%s_%s" % (QAR_TYPES[flag][0],
                                        QAR_TYPES[flag][1])
        self.acft = QAR_TYPES[flag][0]
        self.qar = QAR_TYPES[flag][1]
        self.result = None
        self.progress_bar = progress_bar
        self.define_file_opening()

        self.progress_bar.Show()
        self.progress_bar.SetValue(15)

    def define_file_opening(self):
        if self.flag in MONSTR_HEADER_TYPES:
            self.open_with_monstr_header()
        elif self.flag in OWN_HEADER_TYPES:
            self.open_with_own_header()
        elif self.flag in NO_HEADER_TYPES:
            self.open_with_no_header()

    def open_with_monstr_header(self):
        qar = MonstrHeader(self.path, self.flag, self.progress_bar)
        self.result = qar

    def open_with_own_header(self):
        if self.flag == 322 or self.flag == 402:
            self.result = CompactFlash(self.path, self.acft_fdr_type)

    def open_with_no_header(self):
        if self.flag == 331:  # boeing
            self.result = B747(self.path, self.flag)
        elif self.flag == 341:  # bur92 an148
            self.result = Bur(self.path)
        elif self.flag == 421:  # bur92 an140
            self.result = Bur(self.path)
        elif self.flag == 402 or self.flag == 4022:  # boeing 737-dfdr-980
            self.result = Boeing737DFDR980(self.path, self.flag)