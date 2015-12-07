import os
import datetime
import struct
from source_data import ARINC_DIRECT, QAR_TYPES
from boeing import Boeing
from processing import PrepareData


class A320(PrepareData):

    """ A320. Creation of parametric file with data being processed """

    def __init__(self, tmp_file_name, param_file_name,
                 progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name, param_file_name,
                             progress_bar, path_to_save, flag)
        self.progress_bar.Show()
        self.progress_bar.SetValue(5)

        source = open(tmp_file_name, "rb")
        # open just created tmp parametric file
        self.source_file = source.read()

        # size of tmp parametric file
        self.param_file_end = len(self.source_file)
        self.progress_bar.SetValue(15)

        # rewrite header to target parametric file
        self.header_to_param_file()
        self.progress_bar.SetValue(25)

        # find mix type scheme
        self.scheme_search()
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)

        source.close()
        self.progress_bar.SetValue(100)


class A320RSU(PrepareData):

    """ A320 RSU (digital data)
        scheme`s search, frames check, flight`s recording """

    def __init__(self, tmp_file_name, param_file_name,
                 progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name, param_file_name,
                             progress_bar, path_to_save, flag)
        self.progress_bar.Show()
        self.progress_bar.SetValue(5)

        source = open(tmp_file_name, "rb")
        # open just created tmp parametric file
        self.source_file = source.read()
        # size of tmp parametric file
        self.param_file_end = len(self.source_file)
        self.progress_bar.SetValue(25)

        self.add_header()
        # find mix type scheme
        self.scheme_search()
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)

        source.close()
        self.progress_bar.SetValue(100)

    def add_header(self):
        """ For flight to be properly recognised by LUCH - add header as one used with Compact Flash
        #header = ['04', '03', '00', '0b', '00', '00', '04', '4e', '01', '00', '01', '01', '07', '01', '01', '15'
                  '00', '70', '83', '66', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00', '00']"""
        dec_header = [4, 3, 0, 11, 0, 0, 4, 78, 1, 0, 1, 1, 7, 1, 1, 21,
                      0, 112, 131, 102, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # header values already converted to dec
        for value in dec_header:
            # convert binary string to int
            #value = int((''.join(format(ord(symbol), 'b') for symbol in each)), 2)
            # int takes 4 byte, but we need only first one
            to_write = (struct.pack("i", value))[:1]
            # as the rest are 0s in our case, because
            # we input only 8 bits (one byte)
            self.param_file.write(to_write)


class A320RSUFlightsSearch(Boeing):
    """ A320 RSU. Find flights to display"""
    sw_one = ARINC_DIRECT[1]
    sw_two = ARINC_DIRECT[2]

    def __init__(self, path, flag):
        Boeing.__init__(self, path, flag)
        self.path = path
        self.flag = flag  # define fdr type
        self.end_pattern = [0] * 20
        self.start_pattern = [255] * 20
        self.data = open(self.path, "rb").read()
        self.data_len = os.stat(self.path).st_size
        self.start_index = None
        self.init_date = None
        self.end_flag = False
        self.data_start = None
        self.record_end_index = False
        self.frame_len = QAR_TYPES[flag][2]
        self.subframe_len = self.frame_len / 4
        self.frame_duration = QAR_TYPES[flag][3]  # sec
        self.flight_first_three_frames = []
        self.pattern = None
        self.end_date = []
        self.bytes_counter = 0
        self.packet_size = self.frame_len * 4

        self.find_start()
        self.find_flights()
        self.get_flight_intervals()
        self.get_durations()

        self.get_date_time()  # get date time now
        self.get_flight_ends()

    def find_start(self):
        """ technical info goes at the beginning - something like header (4 of them)
        then comes a lot of FF FF FF
        after that find the first set of 00 00 00 00 00 (about 20) and
        the first flight comes after that """
        i = 0
        for each in self.data:
            if ord(each) == 255:
                i += 1
            else:
                i = 0
            self.bytes_counter += 1
            if i == 20:
                break  # found FF FF FF ...
        # find start of data after FF FF FF ...
        for each in self.data[self.bytes_counter:]:
            if ord(each) != 255:
                self.bytes_counter += 1
                self.data_start = self.bytes_counter
                break
            else:
                self.bytes_counter += 1
        self.flights_start.append(self.data_start)

    def find_flights(self):
        """ find all flights starts """
        while self.bytes_counter < len(self.data):
            # start looking from current position
            self.find_flight_start(self.data[self.bytes_counter:])

    def find_flight_start(self, data_range):
        """ different fdr types has different pattern of flight end\start
            BDV type has end pattern of ones """
        i = 0
        pattern = 7
        for each in data_range:
            if ord(each) == 255:
                i += 1
            else:
                i = 0
            self.bytes_counter += 1
            if i == pattern:
                self.append_start()

    def append_start(self):
        """ append flight start to flights start list"""
        self.flights_start.append(self.bytes_counter)
        # ensure cases when zeroes = 40 and more
        # increase position to pass zeroes
        #self.bytes_counter += 40
        return

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start):
            try:
                self.flight_intervals.append((self.flights_start[i], self.flights_start[i+1]))
            except:
                self.flight_intervals.append((self.flights_start[i], self.data_len))
            i += 1
        # take all flights as a whole record from data start till data end
        #self.flight_intervals.append((self.flights_start[0], self.data_len))

    def get_date_time(self):
        """ get date and time at the moment of flight creation """
        date = datetime.datetime.now()
        for each in self.flight_intervals:
            self.start_date.append(date)
            self.end_date.append(date)

    def get_durations(self):
        for each in self.flight_intervals:
            flight_duration = (each[1] - each[0]) // 768 * self.frame_duration
            self.durations.append(flight_duration)
