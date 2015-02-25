import struct
import os
from source_data import ARINC_REVERSE, ARINC_DIRECT
from source_data import HEADER_SIZE


class DigitalHarvard:

    """ CONVERT RECTANGULAR HARVARD SIGNAL TO TEXT AND BINARY FILE

    This class reads digital rectangular signal, calculate lengths
    of impulses and based on lengths above and below average value
    determine were zeroes and ones. zero is half period (long impulse),
    one has full period (two short impulses).
    duration of one and zero is approximately the same.

    Settings for Boeing 737 4700 - YanAir

    """

    def __init__(self, tmp_file_name, target_file_name, frame_size, subframe_size,
                 progress_bar, path_to_save, flag):
        self.zero = 40  # min number of bytes(length) that determines zero
        self.target_file = open(r"%s" % path_to_save + r"\\" +
                                r"%s" % target_file_name, "wb")
        self.source = open(tmp_file_name, "rb")
        self.sequence = 1000  # sequence of bytes to determine average
        self.start = 0
        self.stop = 0
        self.first_syncword = ARINC_REVERSE[1]
        self.second_syncword = ARINC_REVERSE[2]
        self.third_syncword = ARINC_REVERSE[3]
        self.fourth_syncword = ARINC_REVERSE[4]
        self.frame_in_bits = 3072
        self.sub_frame_bits = 768
        self.source_size = os.stat(tmp_file_name).st_size
        self.frame_size = frame_size
        self.subframe_size = subframe_size
        self.progress_bar = progress_bar
        self.flag = flag
        self.bytes_counter = 0
        self.flight_ord = []
        self.flight_harvard = []
        self.str_data = None
        self.start_index = 0
        self.flight = True
        self.bit_counter = 0
        self.lengths = []
        self.flight_harvard = []
        self.arinc = []

        self.progress_bar.Show()

        self.write_header()
        self.progress_bar.SetValue(15)

        self.find_average()
        self.progress_bar.SetValue(25)

        self.calc_length()
        self.progress_bar.SetValue(35)

        self.convert_to_arinc()
        self.progress_bar.SetValue(65)

        self.get_data_as_str()
        self.progress_bar.SetValue(85)

        self.record_data()
        self.progress_bar.SetValue(100)

    def write_header(self):
        self.target_file.write(self.source.read(HEADER_SIZE))

    def find_average(self):
        """find average value - average level to compare with"""
        summa = sum(map((lambda x: ord(x)), self.source.read(self.sequence)))
        self.average = summa/self.sequence
        # go back by sequence length -> to get at the data beginning
        self.source.seek(HEADER_SIZE, 0)

    def count_upper(self, data, upper_part):
        """count number of bytes above average level"""
        ord_data = ord(data)
        if ord_data >= self.average:
            upper_part += 1
            upper = True
        elif ord_data < self.average:
            self.lengths.append(upper_part)
            upper_part = 1
            upper = False
        return upper_part, upper

    def count_lower(self, data, lower_part):
        """count number of bytes below average level"""
        ord_data = ord(data)
        if ord_data < self.average:
            lower_part += 1
            upper = False
        elif ord_data >= self.average:
            self.lengths.append(lower_part)
            lower_part = 1
            upper = True
        return lower_part, upper

    def calc_length(self):
        """count bytes (length) of pulses and record them"""
        upper_part = 0
        lower_part = 0
        upper = True
        while True:
            data = self.source.read(1)
            if data == '':
                break
            if upper:
                upper_part, upper = self.count_upper(data, upper_part)
            elif not upper:
                lower_part, upper = self.count_lower(data, lower_part)
        # lengths should begin from zero value
        while True:
            if self.lengths[0] < self.zero:
                del self.lengths[0]
            else:
                break

    def convert_to_arinc(self):
        """Convert to arinc (zeros and ones) by lengths"""
        i = 0
        while i < len(self.lengths):
            if self.lengths[i] >= self.zero:  # zero check
                self.flight_harvard.append("0")
                i += 1
            elif self.lengths[i] < self.zero:
                self.flight_harvard.append("1")
                i += 2
            # to create binary file of data
            #if len(self.flight_harvard) == 8:
                #byte_to_str = ''.join(self.flight_harvard)
                #str_to_int = int(byte_to_str, 2)
                #data_to_write = struct.pack("i", str_to_int)
                #self.target_file.write(data_to_write[:1])
                #self.flight_harvard = []

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
                else:
                    self.start_index = self.bit_counter + 1
                    break

    def find_start(self):
        start = self.str_data.find(self.first_syncword, self.start_index)
        if start == -1:
            self.flight = False
            return
        self.start_index = start + 1
        self.bit_counter = start
        return start

    def check_frame(self):
        first_sw = self.bit_counter
        first_subframe = first_sw + self.sub_frame_bits

        second_sw = self.str_data[first_subframe:first_subframe + 12]
        second_subframe = first_subframe + self.sub_frame_bits

        third_sw = self.str_data[second_subframe:second_subframe+12]
        third_subframe = second_subframe + self.sub_frame_bits

        fourth_sw = self.str_data[third_subframe:third_subframe+12]
        fourth_subframe = third_subframe + self.sub_frame_bits

        next_first_syncword = self.str_data[fourth_subframe:fourth_subframe + 12]
        if second_sw == self.second_syncword and \
           third_sw == self.third_syncword and \
           fourth_sw == self.fourth_syncword and \
           next_first_syncword == self.first_syncword:

            return True
        else:
            return False

    def write_frame(self, frame):

        i = 0
        while i < len(frame):
            word = frame[i:i+12]
            reverse_word = "0000" + word[::-1]
            #direct_word = "0000" + word
            bytes_to_write = [reverse_word[8:], reverse_word[0:8]]
            #bytes_to_write = [direct_word[0:8], direct_word[8:]]
            for each in bytes_to_write:
                str_to_int = int(each, 2)
                data_to_write = struct.pack("i", str_to_int)
                self.target_file.write(data_to_write[:1])
            i += 12