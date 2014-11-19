from SAAB340 import SAAB
from airbus import A320
import win32api
from tester import TesterU32
from msrp import MSRP12
from header_frames import HeaderFrameSearchWrite

QAR_TYPES = {0: "MSRP-12",  # An26
             14: "Tester-2",  # An32
             70: "Compact Flash",  # A320
             71: "QAR-B747",
             72: "BUR-92",  # An148
             73: "QAR-2100",
             74: "QAR-4100",
             75: "QAR-4120",
             76: "QAR-4700",
             254: "QAR SAAB",
             255: "QAR-R"}


class Flight:

    """this class takes start and end indexes of flight
    and make either RAW file or send data further
    to be processed according to QAR type"""

    def __init__(self, gui_progress, start, end, path, name, qar_type, path_to_save, flag):
        self.progress_bar = gui_progress
        self.start = start
        self.end = end
        self.path = path
        self.name = name
        self.path_to_save = path_to_save
        self.flag = flag
        self.qar_type = qar_type
        if self.flag == "a320_cf":
            self.prepare_cf_file()
            self.make_flight()
        elif self.flag == "b747_qar" or self.flag == "an148_bur92":
            self.get_flight()
            self.save_flight()
        elif self.flag == "qar":
            self.get_flight()
            self.make_flight()
        elif self.flag == "a320_qar":
            self.qar_type = self.flag
            self.get_flight()
            self.make_flight()
        elif self.flag == "an32_testerU32":
            self.get_flight()
            self.make_flight()
        elif self.flag == "an26_msrp12":
            self.get_flight()
            self.make_flight()

    def get_flight(self):
        """ get the whole flight from source file """
        header = 128
        eof = [255] * 16
        data = open(self.path, "rb")
        if self.end == 0:
            data.seek(self.start + header)
            counter = header
            dat = data.read(15)
            part = [ord(each) for each in dat]
            while True:
                part.append(ord(data.read(1)))
                if part == eof:
                    break
                else:
                    counter += 1
                    part = part[1:]
            data.seek(self.start)
            length = counter
            self.flight = data.read(length)
        else:
            data.seek(self.start)
            length = self.end - self.start
            self.flight = data.read(length)

    def make_flight(self):
        if "raw" in self.name:
            # save raw data in file
            new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + ".bin", "wb")
            new_file.write(self.flight)
        else:
            # make tmp file for future processing
            tmp_file_name = str(win32api.GetTempPath()) + self.name + ".tmp"  # tmp file with flight
            #print("tmp_file_name %s" % tmp_file_name)
            target_file_name = str(self.name) + ".inf"  # target parametric file, mix scheme is applied
            # tmp_bin_file -> interim file with parametric data for SAAB
            # pass it to SAAB only
            tmp_bin_file = str(win32api.GetTempPath()) + self.name + ".bin"
            new_file = open(tmp_file_name, "wb")
            new_file.write(self.flight)
            if self.qar_type == "QAR SAAB":
                saab = SAAB(tmp_file_name, target_file_name, 384, 96,
                            self.progress_bar, self.path_to_save, self.flag, tmp_bin_file)
            elif self.qar_type == "a320_qar" or self.qar_type == "a320_cf":
                a320 = A320(tmp_file_name, target_file_name, 768, 192, self.progress_bar,
                            self.path_to_save, self.flag)
            elif self.qar_type == "Tester-2":  # an32
                tester = HeaderFrameSearchWrite(tmp_file_name, target_file_name, self.progress_bar,
                                   self.path_to_save, self.flag, ["255", "127"], 0)
            elif self.qar_type == "MSRP-12":  # an32
                tester = HeaderFrameSearchWrite(tmp_file_name, target_file_name, self.progress_bar,
                                   self.path_to_save, self.flag, ["255"], 384)

    def prepare_cf_file(self):
        """ Prepares Compact Flash file
        Each cluster begins with header.
        Leave the first header and delete other """
        header = 32  # bytes
        data = open(self.path, "rb")  # path to tmp file containing full copy of compact flash
        cluster = 8192  # cluster size in bytes
        data.seek(self.start, 0)
        flight_length = self.end - self.start
        self.flight = data.read(cluster)  # read first header and data till next header
        bytes_counter = cluster
        while bytes_counter < flight_length:
            data.seek(header, 1)
            self.flight += data.read(cluster - header)
            bytes_counter += cluster

    def save_flight(self):
        """save flight as it is in file"""
        new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + ".inf", "wb")
        new_file.write(self.flight)


