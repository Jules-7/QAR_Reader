#-*-coding: utf-8-*-
import os
import struct
import datetime
from source_data import QAR_TYPES

MONSTR = 'MONSTR'  # monstr header start indicator
CLUSTER = 32768  # cluster size in bytes 32 * 1024
COUNTER_INCREMENT = float(4294967295)
HEADER_SIZE = 128  # B


class MonstrHeader():

    """ - find flights
        - check headers
        - extract information from headers
        - provide with all technical/additional information

        COMPLETE HEADER DESCRIPTION IN initialization.py """

    def __init__(self, path, flag, progress_bar):
        self.path = path
        self.info = "%s_%s" % (QAR_TYPES[flag][0],
                               QAR_TYPES[flag][1])
        self.acft = QAR_TYPES[flag][0]
        self.qar_type = QAR_TYPES[flag][1]
        self.frame_size = QAR_TYPES[flag][2]  # in Bytes
        self.frame_duration = QAR_TYPES[flag][3]  # in seconds
        self.dat = open(self.path, 'rb')
        self.file_len = os.stat(self.path).st_size
        self.index = 0  #524288  # index of records beginning in bytes
        self.flights_start = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.init_date = None
        self.start_date = []
        self.start_date_str_repr = []
        self.durations = []
        self.end_date = []
        self.corrupted_header = []
        self.progress_bar = progress_bar

        self.find_flights()
        self.progress_bar.SetValue(25)

        if self.flights_start:
            self.get_flight_intervals()
            self.progress_bar.SetValue(45)

            if self.corrupted_header:
                self.correct_flight_intervals()
            '''# count durations by frames
            if self.info == "a320_qar" or self.qar_type == "msrp12" or self.info == "b737_4700"\
                    or self.info == "s340_qar_sound" or self.info == "s340_qar_no_sound" \
                    or self.info == "an74_bur3" or self.info == "an74_bur3_code":
                self.get_durations_optional(self.info)
            else:
                # count durations using QAR header -> processor time
                self.get_durations()'''
            self.get_durations()
            self.progress_bar.SetValue(65)

            #self.get_qar_type()
            self.dat.close()
            self.progress_bar.SetValue(85)

        self.check_dates()
        # additional
        # write current date (flight start date) to header
        # if it has not been written before
        # in bytes: 70, 72, 74, 76, 78, 80
        # symmetrically + 2 lines (16 columns) to date of initialization
        self.add_date_to_header()
        self.progress_bar.SetValue(100)

    def is_flight(self):
        """ check for MONSTR and if so record header """
        flight = self.dat.read(6)
        if flight == MONSTR:
            header = self.dat.read(122)
            check = self.check_header(header)
            if check:  # header is valid
                if not self.init_date:
                    self.get_initial_date(header)
                self.flights_start.append(self.index)
                self.get_current_date(header)
                self.headers.append(header)
            else:  # header is not valid
                if len(self.flights_start) > 1:
                    # but we need to take it as an end of previous flight
                    self.corrupted_header.append((self.flights_start[-1], self.index))
                else:
                    pass
        self.index += CLUSTER

    def find_flights(self):

        """ find all flights indexes """

        while self.index < self.file_len:
            self.dat.seek(self.index)
            self.is_flight()

    def get_flight_intervals(self):

        """ flight intervals may be found either by headers index
            or by checking for 'end pattern'
            different types have different end patterns

            - bur3 flight ends either by zeroes or by next header
              last flight ends either by zeroes or by file end """

        if self.info == "b737_4700" or self.info == "an74_bur3":
            i = 0
            for each in self.flights_start:
                try:
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.flights_start[i+1]))
                except IndexError:  # last flight(header) -> no more headers after that
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.file_len))
                i += 1

        elif self.info == "an74_bur3_code" or self.info == "a320_qar" \
                or self.qar_type == "msrp12" or self.info == "s340_qar_sound":
            #if self.info == "an74_bur3"
            i = 0
            for each in self.flights_start:
                try:  # current header index and next one
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.flights_start[i+1]))
                except IndexError:  # last flight(header) -> no more headers after that
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.get_flight_end(self.flights_start[i],
                                                                      self.file_len)))
                i += 1

        # msrp12 flights end by header
        # testerU32 flights end by FF*512
        # s340-qar flights end by FF*20 or 00*20 or header
        elif self.qar_type == "testerU32" or self.info == "s340_qar_no_sound":
            i = 0
            for each in self.flights_start:
                try:
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.get_flight_end(self.flights_start[i],
                                                                      self.flights_start[i+1])))
                except IndexError:  # last flight(header) -> no more headers after that
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.get_flight_end(self.flights_start[i],
                                                                      self.file_len)))
                i += 1

        else:  # for other qar types
            i = 0
            for each in self.flights_start:
                try:
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.flights_start[i+1]))
                except IndexError:  # last flight(header) -> no more headers after that
                    self.flight_intervals.append((self.flights_start[i],
                                                  self.get_flight_end(self.flights_start[i],
                                                                      self.file_len)))
                i += 1
        #print(self.flight_intervals)

    def correct_flight_intervals(self):

        """ in case we have corrupted headers -> they do not define valid flight
            but they indicate the real end of previous flight
            that`s why we need to take them as real flights ends at flights intervals"""

        i = 0
        for start, end in self.flight_intervals[:-2]:
            for start_cor, end_cor in self.corrupted_header:
                if start == start_cor:
                    self.flight_intervals[i] = (start, end_cor)
            i += 1

    def get_durations(self):

        """ duration is counted by frames, not by counter value from header

            BUR3 - data is stored in Harvard coding -> not ARINC
            as data is to be processed and reduced in volume, to get approximate
            duration -> 1 frame (384B) count as 0.12 sec, although actually
            its 1 frame - 1 sec """

        i = 0
        for each in self.start_date:
            bytes_in_flight = self.flight_intervals[i][1] - self.flight_intervals[i][0]
            #frames_in_flight = bytes_in_flight / bytes_in_frame
            frames_in_flight = bytes_in_flight / self.frame_size

            # difference may be not whole number,
            # not to get seconds as decimal fraction -> round it

            #duration_in_sec = round(frames_in_flight * frame_duration)
            duration_in_sec = round(frames_in_flight * self.frame_duration)
            end = each + datetime.timedelta(seconds=duration_in_sec)
            self.end_date.append(end)
            self.durations.append(duration_in_sec)
            i += 1

    def get_flight_end(self, start, end):

        """ flight end is determined by either set of 00 or FF of different length
            depending of qar type"""

        self.dat.seek(start + HEADER_SIZE)
        pattern_size = 20
        bytes_counter = 0

        if self.qar_type == "msrp12" or self.qar_type == "testerU32":
            pattern_size = 512

        elif self.info == "an74_bur3" or self.info == "an74_bur3_code":
            pattern_size = 384  # bytes in frame

        elif self.info == "a320_qar":
            pattern_size = 768

        elif self.info == "b737_4700":
            pattern_size = 768*2

        end_sign_ff = ['255'] * pattern_size
        end_sign_zeroes = ['0'] * pattern_size

        while bytes_counter < (end - start - pattern_size):
            next_frame = self.dat.read(pattern_size)
            if next_frame == "":
                return start + bytes_counter
            bytes_counter += pattern_size

            bytes_to_check = [str(ord(each)) for each in next_frame]
            if bytes_to_check == end_sign_ff or bytes_to_check == end_sign_zeroes:
                bytes_counter -= pattern_size
                break
            else:
                bytes_to_check = []
                #self.dat.seek(-(pattern_size/2), 1)
                #bytes_counter -= pattern_size/2
        return start + bytes_counter

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

    def check_header(self, header):

        """ if header is corrupted - filled with ff -
            we don`t take it as valid flight start """

        counter = 0
        for each in header:
            if ord(each) == 255:
                counter += 1
            else:
                counter = 0
            if counter == 16:
                return False
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

        """ date in string format """

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

    '''def get_qar_type(self):
        qar_type = ord(self.headers[0][4])
        for key, value in QAR_TYPES.iteritems():
            if qar_type == key:
                self.qar_type = value'''

    def add_date_to_header(self):

        """ add each flight start date to its header inside CLU-0003.DAT file
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