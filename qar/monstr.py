#-*-coding: utf-8-*-
import os
import struct
import datetime

MONSTR = 'MONSTR'
CLUSTER = 32768  # cluster size in bytes
COUNTER_INCREMENT = float(4294967295)
QAR_TYPES = {0: "msrp12",  # An26
             11: "bur3",  # an74
             14: "testerU32",  # An32, an72
             70: "Compact Flash",  # A320
             71: "QAR-B747",
             72: "bur92",  # An148
             73: "QAR-2100",
             74: "QAR-4100",
             75: "QAR-4120",
             76: "QAR-4700",
             254: "QAR SAAB",
             255: "QAR-R"}


class MonstrHeader():

    """ - find flights
        - check headers
        - extract information from headers
        - provide with all technical/additional information

        COMPLETE HEADER DESCRIPTION IN initialization.py """

    def __init__(self, path, info=None):
        self.path = path
        self.info = info
        self.dat = open(self.path, 'rb')
        self.file_len = os.stat(self.path).st_size
        self.index = 524288  # index of records beginning in bytes
        self.cluster = 32 * 1024  # size of cluster
        self.flights_start = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.qar_type = None
        self.init_date = None
        self.add_current_date = False
        self.start_date = []
        self.start_date_str_repr = []
        self.durations = []
        self.end_date = []
        self.find_flights()
        if self.flights_start:
            self.get_flight_intervals()
            # count durations by frames
            if self.info == "a320_qar" or self.info == "an26_msrp12" or self.info == "b737_4700":
                self.get_durations_optional(self.info)
            else:
                # count durations using QAR header -> processor time
                self.get_durations()
            self.get_qar_type()
            self.dat.close()
            # additional
            # write current date (flight start date) to header
            # if it has not been written before
            # in bytes: 70, 72, 74, 76, 78, 80
            # symmetrically + 2 lines (16 columns) to date of initialization
        self.check_dates()
        if self.add_current_date:  # True means it is necessary
        # to write current date to header
            self.add_date_to_header()


    def is_flight(self):
        """ check for MONSTR and if so record header """
        flight = self.dat.read(6)
        if flight == MONSTR:
            header = self.dat.read(122)
            check = self.check_header(header)
            if check:
                if not self.init_date:
                    self.get_initial_date(header)
                self.flights_start.append(self.index)
                self.get_current_date(header)
                self.headers.append(header)
        self.index += self.cluster

    def find_flights(self):
        """ find all flights indexes """
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
                self.flight_intervals.append((self.flights_start[i],
                                              self.flights_start[i + 1]))
            except IndexError:
                self.flight_intervals.append((self.flights_start[i],
                                              self.get_last_flight_end(self.flights_start[i])))
            i += 1

    def get_durations(self):
        i = 0
        byte = 8
        for each in self.headers:
            dimension = self.process_counter(self.headers[i][5])
            # bits/bytes in channel
            channel = self.process_counter(self.headers[i][7], self.headers[i][6])
            # channels in frame
            frame = self.process_counter(self.headers[i][9], self.headers[i][8])
            frame_rate = self.process_counter(self.headers[i][11], self.headers[i][10])
            if dimension == 0:  # bytes
                bytes_in_frame = frame * channel
            elif dimension == 1:  # bits
                bytes_in_frame = (frame * channel) / byte

            bytes_in_flight = self.flight_intervals[i][1] - self.flight_intervals[i][0]
            frames_in_flight = bytes_in_flight / bytes_in_frame
            # difference may be not whole number,
            # not to get seconds as decimal fraction -> round it
            duration_in_sec = round(frames_in_flight / frame_rate)
            end = self.start_date[i] + datetime.timedelta(seconds=duration_in_sec)
            self.end_date.append(end)
            #duration = time.strftime('%H h %M m %S s', time.gmtime(duration_in_sec))
            self.durations.append(duration_in_sec)
            i += 1

    def get_durations_optional(self, acft):
        """ for these aircraft types at which flight duration is counted by frames,
        not by counter value from header"""
        # frame duration for aircraft type in sec
        acft_frame_duration = {"a320_qar": 4,  # 1 frame - 4 sec
                               "an26_msrp12": 0.5,
                               "b737_4700": 4}
        frame_duration = acft_frame_duration[acft]
        i = 0
        for each in self.start_date:
            bytes_in_flight = self.flight_intervals[i][1] - self.flight_intervals[i][0]
            bytes_in_frame = 768
            frames_in_flight = bytes_in_flight / bytes_in_frame
            # difference may be not whole number,
            # not to get seconds as decimal fraction -> round it
            duration_in_sec = round(frames_in_flight * frame_duration)
            end = each + datetime.timedelta(seconds=duration_in_sec)
            self.end_date.append(end)
            self.durations.append(duration_in_sec)
            i += 1

    def get_last_flight_end(self, start):
        """ as there are no headers after last flight
        (which can be used as definite sign of flight end)
        we search for zeroes, which mean that flight has ended """
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
        """ initial date is written in header as it is (by exact value we can see) """
        init_year = '20' + (hex(ord(header[32])))[2:]

        init_month = '0' + (hex(ord(header[34])))[2:] if \
                            len((hex(ord(header[34])))[2:]) == 1 else \
                           (hex(ord(header[34])))[2:]

        init_day = '0' + (hex(ord(header[36])))[2:] if \
                          len((hex(ord(header[36])))[2:]) == 1 else \
                          (hex(ord(header[36])))[2:]

        init_hour = '0' + (hex(ord(header[38])))[2:] if \
                           len((hex(ord(header[38])))[2:]) == 1 else \
                           (hex(ord(header[38])))[2:]

        init_minute = '0' + (hex(ord(header[40])))[2:] if \
                             len((hex(ord(header[40])))[2:]) == 1 else \
                             (hex(ord(header[40])))[2:]

        init_second = '0' + (hex(ord(header[42])))[2:] if \
                             len((hex(ord(header[42])))[2:]) == 1 else \
                             (hex(ord(header[42])))[2:]

        self.init_counter = self.process_counter(header[109], header[108], header[107], header[106])
        # convert to int
        self.init_date = datetime.datetime(int(init_year), int(init_month), int(init_day),
                                           int(init_hour), int(init_minute), int(init_second))
        if not self.add_current_date:
            # if False -> we need to check has current date been written or not
            # if True -> current date has been written in header
            self.check_if_current_date(header)

    def check_if_current_date(self, header):
        """ check if current date has already been written to header """
        curr_year_ord = (hex(ord(header[64])))[2:]
        if curr_year_ord == '0':
            self.add_current_date = True

    def check_header(self, header):
        """ if header is corrupted - filled with ff
        we don`t take it into account"""
        corrupted = '0xff' * 16
        to_check = ''
        for each in header:
            to_check += hex(ord(each))
        if corrupted in to_check:
            return False
        else:
            return True

    def get_current_date(self, header):
        """ flight start date """
        curr_counter = (self.process_counter(header[117], header[116],
                                             header[115], header[114]))
        if curr_counter < self.init_counter:
            curr_counter += COUNTER_INCREMENT
        # difference may be not whole number,
        # not to get seconds as decimal fraction -> round it
        diff = round((curr_counter - self.init_counter)/256)

        '''if curr_counter < self.init_counter:
            curr_counter += COUNTER_INCREMENT
            # difference may be not whole number,
            # not to get seconds as decimal fraction -> round it
            diff = round((curr_counter - self.init_counter)/256)
        else:
            # difference may be not whole number,
            # not to get seconds as decimal fraction -> round it
            diff = round((curr_counter - self.init_counter)/256)'''
        start_date = (self.init_date + datetime.timedelta(seconds=diff))
        self.start_date.append(start_date)
        year, month, day, hour, minute, second = self.str_date_repr(start_date)
        self.start_date_str_repr.append([year, month, day,
                                         hour, minute, second])

    def str_date_repr(self, start_date):
        year = start_date.strftime("%y")
        month = start_date.strftime("%m")
        day = start_date.strftime("%d")
        hour = start_date.strftime("%H")
        minute = start_date.strftime("%M")
        second = start_date.strftime("%S")
        return year, month, day, hour, minute, second

    def process_counter(self, *args):
        """ processing (transformation) of hex value to decimal """
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
        for key, value in QAR_TYPES.iteritems():
            if qar_type == key:
                self.qar_type = value

    def add_date_to_header(self):
        """ add each flight start date to its header  inside CLU-0003.DAT file
        by overwriting empty bytes """
        #current_date_bytes = [70, 72, 74, 76, 78, 80]
        with open(self.path, "r+") as source:
            i = 0
            for each in self.flights_start:
                source.seek(each, 0)  # get at the beginning of flight
                source.seek(69, 1)  # get before byte 70 to start record current date
                data_for_header = []
                cur_date = self.start_date_str_repr[i]
                #----- year --------
                year_bin = self.get_hex_repr(cur_date[0])
                data_for_header.append(year_bin)

                #----- month ------
                month_bin = self.get_hex_repr(cur_date[1])
                data_for_header.append(month_bin)

                #----- day ------
                day_bin = self.get_hex_repr(cur_date[2])
                data_for_header.append(day_bin)

                #----- hour -----
                hour_bin = self.get_hex_repr(cur_date[3])
                data_for_header.append(hour_bin)

                #----- minute ----
                minute_bin = self.get_hex_repr(cur_date[4])
                data_for_header.append(minute_bin)

                #----- sec ------
                second_bin = self.get_hex_repr(cur_date[5])
                data_for_header.append(second_bin)

                data = [str(each) for each in data_for_header]

                for value in data:
                    dat_int = int(value, 2)
                    dat_write = (struct.pack("i", dat_int))[:1]
                    source.seek(1, 1)  # seek next byte before byte to write
                    source.write(dat_write)
                i += 1

    def get_hex_repr(self, value):
        """ processing (transformation) of integer in string representation
        to its binary repr """
        hex_value = '0x%s' % value
        int_value = int(hex_value, 16)
        bin_value = bin(int_value)
        return bin_value

    def check_dates(self):
        """ in case calendar/clock is out of order,
            date becomes less than previous one.
            in this case processor timer is reset to zero.
            during this check in case datetime is less than previous one,
            flight start/end datetime is set to 2014.0.0 0:0:0 """
        checked_start_dates = [self.start_date[0]]
        i = 0
        while i <= len(self.start_date):
            try:
                if self.start_date[i] > self.start_date[i+1]:
                    zero_date = datetime.datetime(year=2014, month=1, day=1,
                                                  hour=0, minute=0, second=0)
                    checked_start_dates.append(zero_date)
                    self.end_date[i+1] = zero_date
                    # flight start datetime data prepared to be written into header
                    year, month, day, hour, minute, second = self.str_date_repr(zero_date)
                    self.start_date_str_repr[i+1] = [year, month, day,
                                                     hour, minute, second]
                else:
                    checked_start_dates.append(self.start_date[i+1])
            except IndexError:
                break
            i += 1
        self.start_date = checked_start_dates