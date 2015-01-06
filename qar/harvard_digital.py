import struct
from bur3 import Bur3


class DigitalHarvard:

    """ CONVERT RECTANGULAR HARVARD SIGNAL TO TEXT AND BINARY FILE

    This class reads digital rectangular signal, calculate lengths
    of impulses and based on lengths above and below average value
    determine were zeroes and ones. zero is half period (long impulse),
    one has full period (two short impulses).
    duration of one and zero is approximately the same. """

    def __init__(self):
        self.zero = 5  # min number of bytes(length) that determines zero
        self.path = "E://bur_3_cavok/12291250.wa"
        self.target_file = open("E://bur_3_cavok/12291250_bur_3.dat", "wb")
        self.source = open(self.path, "rb")
        self.header_size = 128
        self.sequence = 1000  # sequence of bytes to determine average
        self.start = 0
        self.stop = 0
        self.syncword = "001001000111"
        self.frame_in_bits = 3072
        #self.source_size = os.stat(tmp_file_name).st_size
        self.frame_size = 512
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

        self.write_header()
        self.find_average()
        self.calc_length()
        self.convert_to_arinc()
        self.get_data_as_str()
        self.record_data()

    def write_header(self):
        self.target_file.write(self.source.read(self.header_size))

    def find_average(self):
        """find average value - average level to compare with"""
        summa = sum(map((lambda x: ord(x)), self.source.read(self.sequence)))
        self.average = summa/self.sequence
        # go back by sequence length -> to get at the data beginning
        self.source.seek(-self.sequence, 1)

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
            #if len(self.harvard) == 8:
                #self.write_result_in_bin()
                #self.harvard = []

    def write_result_in_bin(self):
        """write result in binary format"""
        byte_to_str = ''.join(self.flight_harvard)
        str_to_int = int(byte_to_str, 2)
        data = struct.pack("i", str_to_int)
        self.target_file.write(data[:1])

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

instance = DigitalHarvard()
