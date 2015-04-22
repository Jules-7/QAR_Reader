from monstr import MonstrHeader
from boeing import Boeing737DFDR980, B747
from bur_92 import Bur
from compactFlash import CompactFlash
from source_data import QAR_TYPES, MONSTR_HEADER_TYPES
from source_data import OWN_HEADER_TYPES, NO_HEADER_TYPES


class Redirect(object):

    """ This class redirect to appropriate class
        depending on type of data source (QAR, CF, FDR) and aircraft type"""

    def __init__(self, path, chosen_acft_type, progress_bar):
        self.path = path
        self.chosen_acft_type = chosen_acft_type
        self.acft_fdr_type = "%s_%s" % (QAR_TYPES[chosen_acft_type][0],
                                        QAR_TYPES[chosen_acft_type][1])
        self.acft = QAR_TYPES[chosen_acft_type][0]
        self.qar = QAR_TYPES[chosen_acft_type][1]
        self.result = None
        self.progress_bar = progress_bar
        self.define_file_opening()

        self.progress_bar.Show()
        self.progress_bar.SetValue(15)

    def define_file_opening(self):
        if self.chosen_acft_type in MONSTR_HEADER_TYPES:
            self.open_with_monstr_header()
        elif self.chosen_acft_type in OWN_HEADER_TYPES:
            self.open_with_own_header()
        elif self.chosen_acft_type in NO_HEADER_TYPES:
            self.open_with_no_header()

    def open_with_monstr_header(self):
        qar = MonstrHeader(self.path, self.chosen_acft_type, self.progress_bar)
        self.result = qar

    def open_with_own_header(self):
        if self.chosen_acft_type == 322 or self.chosen_acft_type == 402:
            self.result = CompactFlash(self.path, self.acft_fdr_type)

    def open_with_no_header(self):
        if self.chosen_acft_type == 331:  # boeing
            self.result = B747(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 341:  # bur92 an148
            self.result = Bur(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 421:  # bur92 an140
            self.result = Bur(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 402 or self.chosen_acft_type == 4022:  # boeing 737-dfdr-980
            self.result = Boeing737DFDR980(self.path, self.chosen_acft_type)