from SAAB340 import SAAB
from airbus import A320
import os
import win32api

"""this module:
              - finds ARINC 717 syncwords
              - checks integrity of frames
              - return only valid frames"""


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
        if self.flag == "cf":
            self.prepare_cf_file()
            self.make_flight()
        elif self.flag == "boeing_check":
            self.get_flight()
            self.save_flight()
        else:
            self.get_flight()
            self.make_flight()


    def get_flight(self):
        header = 128
        eof = [255] * 16
        data = open(self.path, 'rb')
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
        if "flight" in self.name:
            """make tmp file for future processing"""
            #separator = self.path.rfind('/')
            #new_path = self.path[:separator + 1]
            #file_name = new_path + str(self.name)
            tmp_file_name = str(win32api.GetTempPath()) + self.name + ".tmp"  # tmp file with flight
            print("tmp_file_name %s" % tmp_file_name)
            target_file_name = str(self.name) + ".inf"  # target parametric file, mix scheme is applied
            # pass it to SAAB only
            # interim file with parametric data for SAAB
            tmp_bin_file = str(win32api.GetTempPath()) + self.name + ".bin"
            new_file = open(tmp_file_name, 'wb')
            new_file.write(self.flight)
            #a320 = A320(tmp_file_name, target_file_name, 768, 192, self.progress_bar, self.path_to_save, self.flag)
            saab = SAAB(tmp_file_name, target_file_name, 384, 96,
                        self.progress_bar, self.path_to_save, self.flag, tmp_bin_file)

            '''
            if self.qar_type == "VDR":
                saab = SAAB(tmp_file_name, target_file_name, tmp_param_file, 384, 96,
                self.progress_bar, self.path_to_save, self.flag, tmp_bin_file)
            elif self.qar_type == "":
                a320 = A320(tmp_file_name, target_file_name, 768, 192,
                            self.progress_bar, self.path_to_save, self.flag)'''
        elif "raw" in self.name:
            """save raw data in file"""
            #separ = self.path.rfind('/')
            #new_path = self.path[:separ + 1]
            new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + '.bin', 'wb')
            new_file.write(self.flight)

    def prepare_cf_file(self):
        """ Each cluster begins with header.
        Leave the first header and delete other """
        header = 32  # bytes
        data = open(self.path, 'rb')  # path to tmp file containing full copy of compact flash
        cluster = 8192  # cluster size in bytes
        data.seek(self.start, 0)
        flight_length = self.end - self.start
        self.flight = data.read(cluster)  # read first header and data till next header
        bytes_counter = cluster
        while bytes_counter < flight_length:
            data.seek(header, 1)
            self.flight += data.read(cluster - header)
            bytes_counter += cluster
        #print("flight length before is %s" % flight_length)
        #print("flight length after is %s" % len(flight))

    def save_flight(self):
        """save flight as it is in file"""
        new_file = open(r"%s" % self.path_to_save + r"\\" + str(self.name) + '.inf', 'wb')
        new_file.write(self.flight)


