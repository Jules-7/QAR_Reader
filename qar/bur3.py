import os
import struct
import time


SOURCE = 'ACFT'
if SOURCE == 'BSPI':
    zero = 40  # 29, 2A, 2B
elif SOURCE == 'ACFT':
    zero = 19


class Bur3(object):

    """ Data (Arinc 717) is written as durations (zeros and ones) """

    def __init__(self, tmp_file_name, target_file_name,
                 progress_bar, path_to_save, flag, sw, frame, mode):
        self.source = open(tmp_file_name, "rb")
        self.target_file_name = target_file_name
        self.mode = mode
        self.progress_bar = progress_bar

        self.progress_bar.Show()

        self.path_to_save = path_to_save
        name = (r"%s" % self.path_to_save + r"\\" + r"%s" % self.target_file_name)
        #name_txt = (r"%s" % self.path_to_save + r"\\" + r"result_an74.txt")
        self.target_file = open(name, "wb")

        self.progress_bar.SetValue(5)

        #self.target_txt = open(name_txt, "w")
        self.source_size = os.stat(tmp_file_name).st_size
        self.flag = flag
        self.sw = sw
        self.syncword = "001001000111"
        self.frame_size = frame
        self.bytes_counter = 0
        self.flight_ord = []
        self.flight_harvard = []
        self.str_data = None
        self.start_index = 0
        self.flight = True
        self.frame_in_bits = 3072
        self.bit_counter = 0

        self.record_header()

        self.progress_bar.SetValue(15)

        self.convert_to_ord()

        self.progress_bar.SetValue(25)

        self.convert_to_harvard()

        self.progress_bar.SetValue(35)

        self.get_data_as_str()

        self.progress_bar.SetValue(45)

        if self.mode == "code":  # record as it is with no frame check
            self.record_code()
        else:
            self.record_data()

        self.progress_bar.SetValue(85)
        #self.target_file.close()
        #self.target_txt.close()

    def record_header(self):
        header = self.source.read(128)
        self.bytes_counter += 128
        self.target_file.write(header)

    def convert_to_ord(self):
        while self.bytes_counter < self.source_size:
            byte = self.source.read(1)
            if byte == '':
                break
            if ord(byte) > zero:
                self.flight_ord.append(0)
                self.bytes_counter += 1
            elif ord(byte) == 0:
                self.flight_ord.append(0)
                self.bytes_counter += 1
            else:
                self.flight_ord.append(1)
                self.bytes_counter += 1

    def convert_to_harvard(self):
        p = 0
        while p < len(self.flight_ord):
            if self.flight_ord[p] == 0:
                self.flight_harvard.append("0")
                p += 1
            else:
                self.flight_harvard.append("1")
                p += 2

    def get_data_as_str(self):
        self.str_data = ''.join(self.flight_harvard)

    def record_data(self):
        while self.flight:
            syncword = self.find_start()
            while syncword:
                checked = self.check_frame()
                if checked:
                    frame = self.str_data[self.bit_counter:self.bit_counter +
                                                           self.frame_in_bits]
                    self.bit_counter += self.frame_in_bits
                    self.write_frame(frame)
                    self.start_index = self.bit_counter
                    #flight = False
                else:
                    self.start_index = self.bit_counter + 1
                    break

    def find_start(self):
        start = self.str_data.find(self.syncword, self.start_index)
        if start == -1:
            self.flight = False
            return
        self.start_index = start + 1
        self.bit_counter = start
        return start

    def check_frame(self):
        end_of_frame = self.bit_counter + self.frame_in_bits
        next_syncword = self.str_data[end_of_frame:end_of_frame + 12]
        if next_syncword == self.syncword:
            return True
        else:
            return False

    def write_frame(self, frame):
        i = 0
        while i < len(frame):
            word = frame[i:i+12]
            reverse_word = "0000" + word[::-1]
            bytes_to_write = [reverse_word[0:8], reverse_word[8:]]
            for each in bytes_to_write:
                str_to_int = int(each, 2)
                data_to_write = struct.pack("i", str_to_int)
                self.target_file.write(data_to_write[:1])
            i += 12

    def record_code(self):
        while self.bit_counter < len(self.str_data):
            frame = self.str_data[self.bit_counter:self.bit_counter +
                                                           self.frame_in_bits]
            self.bit_counter += self.frame_in_bits
            self.write_frame(frame)
            self.start_index = self.bit_counter