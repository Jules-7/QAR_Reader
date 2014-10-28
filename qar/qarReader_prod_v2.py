#-*-coding: utf-8-*-
import os
import time
import datetime

"""this module:
- finds flight
- checks headers
- determines information from headers
- return all technical/additional information"""

monstr = 'MONSTR'
cluster = 32768  # cluster size in bytes
counter_increment = float(4294967295)
qar_types = {0: u"ЭБН-12",
             1: u"ЭБН-64",
             5: u"ЭБН-Т-М",
             6: u"ЭБН-Т-Л",
             10: u"ЭБН-Б-1",
             11: u"ЭБН-Б-3",
             14: u"ЭБН-Т-2",
             21: u"CFDR-42",
             22: u"ЭБН САРПП",
             254: u"VDR",
             255: u"ЭБН-Р"}


class QARReader():

    def __init__(self, path):
        self.path = path
        self.dat = open(self.path, 'rb')
        self.file_len = os.stat(self.path).st_size
        self.index = 524288  # index of records beginning in bytes
        self.flights_start = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.qar_type = None
        self.init_date = None
        self.start_date = []
        self.durations = []
        self.end_date = []
        self.find_flights()
        self.get_flight_intervals()
        self.get_durations()
        self.get_qar_type()
        self.dat.close()

    def is_flight(self):
        ''' check for MONSTR and if so record header '''
        flight = self.dat.read(6)
        if flight == monstr:
            header = self.dat.read(122)
            check = self.check_header(header)
            if check:
                if not self.init_date:
                    self.get_initial_date(header)
                self.flights_start.append(self.index)
                self.get_current_date(header)
                self.headers.append(header)
        self.index += cluster

    def find_flights(self):
        ''' find all flights indexes '''
        while self.index < self.file_len:
            if self.index == 524288:
                self.dat.seek(524288)
                self.is_flight()
            else:
                self.dat.seek(self.index)
                self.is_flight()

    def get_flight_intervals(self):
        i = 0
        for each in self.flights_start:
            try:
                self.flight_intervals.append((self.flights_start[i], self.flights_start[i + 1]))
            except IndexError:
                self.flight_intervals.append((self.flights_start[i],
                                              self.get_last_flight_end(self.flights_start[i])))
            i += 1

    def get_durations(self):
        i = 0
        byte = 8
        for each in self.headers:
            dimension = self.process_counter(self.headers[i][5])  # dimension
            channel = self.process_counter(self.headers[i][7], self.headers[i][6])  # bits/bytes in channel
            frame = self.process_counter(self.headers[i][9], self.headers[i][8])  # channels in frame
            frame_rate = self.process_counter(self.headers[i][11], self.headers[i][10])
            if dimension == 0:  # bytes
                bytes_in_frame = frame * channel
            elif dimension == 1:  # bits
                bytes_in_frame = (frame * channel) / byte

            bytes_in_flight = self.flight_intervals[i][1] - self.flight_intervals[i][0]
            frames_in_flight = bytes_in_flight / bytes_in_frame
            duration_in_sec = frames_in_flight / frame_rate
            end = self.start_date[i] + datetime.timedelta(seconds=duration_in_sec)
            self.end_date.append(end)
            #duration = time.strftime('%H h %M m %S s', time.gmtime(duration_in_sec))
            self.durations.append(duration_in_sec)
            i += 1

    def get_last_flight_end(self, start):
        header = 128
        self.dat.seek(start + header)
        check_twenty = ''
        counter = 0
        end_sign = '00000000000000000000'
        while True:
            next_byte = self.dat.read(1)
            if next_byte == "":
                return start + counter
            counter += 1
            if ord(next_byte) == 0:
                next_twenty_byte = self.dat.read(20)
                counter += 20
                for each in next_twenty_byte:
                    check_twenty += str(ord(each))
                if check_twenty == end_sign:
                    break
                else:
                    check_twenty = ''
        return start + counter


    def get_initial_date(self, header):
        init_year = '20' + (hex(ord(header[32])))[2:]
        init_month = '0' + (hex(ord(header[34])))[2:] if len((hex(ord(header[34])))[2:]) == 1 else (hex(ord(header[34])))[2:]
        init_day = '0' + (hex(ord(header[36])))[2:] if len((hex(ord(header[36])))[2:]) == 1 else (hex(ord(header[36])))[2:]
        init_hour = '0' + (hex(ord(header[38])))[2:] if len((hex(ord(header[38])))[2:]) == 1 else (hex(ord(header[38])))[2:]
        init_minute = '0' + (hex(ord(header[40])))[2:] if len((hex(ord(header[40])))[2:]) == 1 else (hex(ord(header[40])))[2:]
        init_second = '0' + (hex(ord(header[42])))[2:] if len((hex(ord(header[42])))[2:]) == 1 else (hex(ord(header[42])))[2:]

        self.init_counter = self.process_counter(header[109], header[108], header[107], header[106])
        # convert to int
        self.init_date = datetime.datetime(int(init_year), int(init_month), int(init_day),
                                           int(init_hour), int(init_minute), int(init_second))

    def check_header(self, header):
        corrupted = '0xff' * 16
        to_check = ''
        for each in header:
            to_check += hex(ord(each))
        if corrupted in to_check:
            return False
        else:
            return True

    def get_current_date(self, header):
        curr_counter = (self.process_counter(header[117], header[116],
                                             header[115], header[114]))
        if curr_counter < self.init_counter:
            curr_counter += counter_increment
            diff = (curr_counter - self.init_counter)/256
        else:
            diff = (curr_counter - self.init_counter)/256
        self.start_date.append((self.init_date + datetime.timedelta(seconds=diff)))

    def process_counter(self, *args):
        counter = '0x'
        for each in args:
            if len((hex(ord(each)))[2:]) == 1:
                counter += '0' + (hex(ord(each)))[2:]
            else:
                counter += (hex(ord(each)))[2:]
        current_counter = int(counter, 16)
        return current_counter

    def get_qar_type(self):
        qar_type = ord(self.headers[0][4])
        for key, value in qar_types.iteritems():
            if qar_type == key:
                self.qar_type = value