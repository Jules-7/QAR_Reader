import win32api
from SAAB340 import SAAB
from airbus import A320
from bur3 import Bur3, Bur3Analog
from boeing import B737
from header_frames import HeaderFrameSearchWrite
from harvard_digital import DigitalHarvard
from source_data import QAR_TYPES, HEADER_SIZE
from bur_92 import BUR92AN140

RESOLUTION = ".inf"


class Flight:

    """ This class takes start and end indexes of the flight
        and make either a RAW file or pass data further
        to be processed according to the QAR type """

    def __init__(self, gui_progress, start, end, path, name,
                 chosen_acft_type, path_to_save, optional_arg=None):
        self.progress_bar = gui_progress
        self.start = start
        self.end = end
        self.path = path
        self.name = name
        self.chosen_acft_type = chosen_acft_type
        self.acft = QAR_TYPES[chosen_acft_type][0]
        self.qar_type = QAR_TYPES[chosen_acft_type][1]
        self.flag = self.acft + "_" + self.qar_type
        self.path_to_save = path_to_save
        self.optional_arg = optional_arg

        if self.qar_type == "cf":
            self.prepare_cf_file()
            self.make_flight()

        elif self.flag == "b747_qar" or self.flag == "an148_bur92":
            self.get_flight()
            self.save_flight()

        elif self.flag == "b747_4700":
            tmp_file_name = self.prepare_and_get_flight()
            self.make_flight(tmp_file_name)

        elif self.flag == "an140_bur92":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "qar":
            self.get_flight()
            self.make_flight()

        elif self.acft == "s340":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "testerU32":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "msrp12" or self.qar_type == "msrp64" or self.qar_type == "msrp64_viewer":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "bur3":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "bur3_code":
            self.get_flight()
            self.make_flight()

        elif self.qar_type == "bur3_analog":
            self.get_flight()
            self.make_flight()

        elif self.flag == "b737_4700":
            self.get_flight()
            self.make_flight()

        elif self.flag == "b737_qar":
            self.save_raw()

        elif (self.flag == "b737_dfdr_980" or self.flag == "b737_dfdr_980_BDB" or
              self.flag == "b737_dfdr_980_BDO" or self.flag == "b737_dfdr_980_BDV"):
            self.get_flight()
            self.make_flight()

    def get_flight(self):
        """ get the whole flight from source file """
        #eof = [255] * 16
        eof = [0] * 40
        data = open(self.path, "rb")
        if self.end == 0:
            data.seek(self.start + HEADER_SIZE)
            counter = HEADER_SIZE
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

    def make_flight(self, tmp_file_name=None):
        global RESOLUTION
        if "raw" in self.name:
            # save raw data in file
            new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + ".bin", "wb")

            new_file.write(self.flight)
        else:
            # make tmp file containing the flight for future processing
            if not tmp_file_name:
                tmp_file_name = str(win32api.GetTempPath()) + self.name + ".tmp"
            if QAR_TYPES[self.chosen_acft_type][0] == "an140":
                RESOLUTION = ".txt"
            target_file_name = str(self.name) + RESOLUTION
            new_file = open(tmp_file_name, "wb")
            new_file.write(self.flight)
            new_file.close()

            if self.flag == "s340_qar_sound":
                # tmp_bin_file is used for storing parametric information
                # extracted from source
                # used for qar with sound only
                tmp_bin_file = str(win32api.GetTempPath()) + self.name + ".bin"
                saab = SAAB(tmp_file_name, target_file_name,
                            self.progress_bar, self.path_to_save,
                            self.chosen_acft_type, tmp_bin_file)

            elif self.flag == "s340_qar_no_sound":
                saab = SAAB(tmp_file_name, target_file_name,
                            self.progress_bar, self.path_to_save,
                            self.chosen_acft_type)

            elif self.acft == "a320":
                a320 = A320(tmp_file_name, target_file_name,
                            self.progress_bar, self.path_to_save,
                            self.chosen_acft_type)

            elif self.qar_type == "testerU32":  # an32, an72
                tester = HeaderFrameSearchWrite(tmp_file_name, target_file_name,
                                                self.progress_bar,
                                                self.path_to_save,
                                                self.flag, ["255", "127"], 0)

            elif self.qar_type == "msrp12" or self.qar_type == "msrp64" or self.qar_type == "msrp64_viewer":  # an26, il76
                tester = HeaderFrameSearchWrite(tmp_file_name, target_file_name,
                                                self.progress_bar,
                                                self.path_to_save,
                                                self.flag, ["255"], 384)

            # current version goes as analog to digital signal conversion
            elif self.qar_type == "bur3":  # an74
                bur = Bur3(tmp_file_name, target_file_name, self.progress_bar,
                           self.path_to_save, self.chosen_acft_type, mode="ord")

            elif self.qar_type == "bur3_code":  # an74
                bur = Bur3(tmp_file_name, "code_" + target_file_name,
                           self.progress_bar, self.path_to_save,
                           self.chosen_acft_type, mode="code")

            elif self.qar_type == "bur3_analog":  # an74
                bur = Bur3Analog(tmp_file_name, target_file_name,
                                 self.progress_bar, self.path_to_save,
                                 self.chosen_acft_type, self.optional_arg)

            # 768 - bits in subframe, 3072 - bits in frame
            # for now data is recorded in length (Harvard coding)
            elif self.flag == "b737_4700":
                b737 = DigitalHarvard(tmp_file_name, target_file_name, 3072, 768,
                                      self.progress_bar, self.path_to_save, self.flag)

            elif (self.flag == "b737_dfdr_980" or self.flag == "b737_dfdr_980_BDB" or
                          self.flag == "b737_dfdr_980_BDO" or self.flag == "b737_dfdr_980_BDV"):
                b737 = B737(tmp_file_name, target_file_name, self.progress_bar, self.path_to_save,
                            self.chosen_acft_type)
                # file -> cop_centr_head

            elif self.flag == "an140_bur92":
                bur92 = BUR92AN140(tmp_file_name, target_file_name,
                                   self.progress_bar, self.path_to_save,
                                   self.chosen_acft_type)

            elif self.flag == "b747_4700":  # data processing same as for B737
                b747 = B737(tmp_file_name, target_file_name, self.progress_bar, self.path_to_save,
                                            self.chosen_acft_type)

    def prepare_cf_file(self):

        """ Prepares Compact Flash file
            Each cluster begins with header.
            Leave the first header and delete other """

        header = 32  # bytes
        # path to tmp file containing full copy of compact flash
        data = open(self.path, "rb")
        cluster = 8192  # cluster size in bytes
        data.seek(self.start, 0)
        flight_length = self.end - self.start
        # read first header and data till next header
        self.flight = data.read(cluster)
        bytes_counter = cluster
        while bytes_counter < flight_length:
            data.seek(header, 1)
            pp = data.tell()
            self.flight += data.read(cluster - header)
            bytes_counter += cluster

    def save_flight(self):

        """ save flight as it is in file """

        new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + ".inf", "wb")
        new_file.write(self.flight)

    def save_raw(self):  # b737_qar
        source = open(self.path, "rb").read()
        slash = self.path.rfind("\\")
        dot = self.path.rfind('.')
        name_of_file = self.path[slash:dot]
        new_file = open(r"%s" % self.path_to_save + str(name_of_file) + ".inf", "wb")
        new_file.write(source)
        new_file.close()

    def prepare_and_get_flight(self):
        """ each frame starts with 00 04
           need to remove these two bytes (00 04) and 2 bytes before that
           flight starts just with 00 04
           steps:
               - read whole file
               - take out 0004 and 2 bytes before that in each frame
               - record to file
        """
        data = open(self.path, "rb")  # open original file with data
        data.seek(self.start)
        length = self.end - self.start  # get flight length
        frame_length = QAR_TYPES[self.chosen_acft_type][4]  #
        counter_length = 4  # counter at the beginning of frame ?? ?? 00 04
        bytes_counter = 0
        tmp_file_name = str(win32api.GetTempPath()) + "test" + ".tmp"  # create tmp file to store corrected data
        new_file = open(tmp_file_name, "wb")
        data.seek(counter_length - 2, 1)  # get at the index right after 00 04
        bytes_counter += 2
        while bytes_counter < length - frame_length:
            new_file.write(data.read(frame_length - counter_length))  # frame is 512 - counter 4 bytes ?? ?? 00 04
            data.seek(counter_length, 1)
            bytes_counter += frame_length
        new_file.close()
        source_data = open(tmp_file_name, "rb")  # create file with corrected data
        self.flight = source_data.read()
        source_data.close()
        return tmp_file_name