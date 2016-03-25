from monstr import MonstrHeader
from boeing import Boeing737DFDR980, B747Series200, B747Series300
from bur_92 import Bur, BUR1405
from compactFlash import CompactFlash, B767QARFlights, B737QARNG
from msrp64_viewer import MSRP64EBNViewer
from airbus import A320RSUFlightsSearch
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
        elif self.chosen_acft_type == 5011:
            self.result = MSRP64EBNViewer(self.path, self.chosen_acft_type, self.progress_bar)
        elif self.chosen_acft_type == 701:
            self.result = B767QARFlights(self.path, self.acft_fdr_type)
        elif self.chosen_acft_type == 404:
            self.result = B737QARNG(self.path, self.acft_fdr_type)

    def open_with_no_header(self):
        if self.chosen_acft_type == 331:  # boeing
            self.result = B747Series200(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 3312:
            self.result = B747Series300(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 341 or self.chosen_acft_type == 3412:  # bur92 an148
            self.result = Bur(self.path, self.chosen_acft_type, self.progress_bar)
        elif self.chosen_acft_type == 421:  # bur92 an140
            self.result = Bur(self.path, self.chosen_acft_type)
        elif (self.chosen_acft_type == 402 or self.chosen_acft_type == 4022 or
              self.chosen_acft_type == 4031 or self.chosen_acft_type == 4032 or
              self.chosen_acft_type == 4033):  # boeing 737-dfdr-980
            self.result = Boeing737DFDR980(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 323:
            self.result = A320RSUFlightsSearch(self.path, self.chosen_acft_type)
        elif self.chosen_acft_type == 801:
            self.result = BUR1405(self.path, self.chosen_acft_type)