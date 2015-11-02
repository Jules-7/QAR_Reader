#-*-coding: utf-8-*-
import os
import datetime
from source_data import QAR_TYPES
from monstr import MONSTR, HEADER_SIZE

CLUSTER = 32768  # cluster size in bytes 32 * 1024

# --------------------------------------------------------------------
# ------------------------REDO----------------------------------------
# --------------------------------------------------------------------


class MSRP64EBNViewer(object):

    """ - find flights
        - check headers
        - extract information from headers
        - provide with all technical/additional information

        COMPLETE HEADER DESCRIPTION IN initialization.py


        MSRP 64 that has been readout by EBN viewer.

        After viewer it contains only flights. But headers are not at the clusters beginning,
        so it is not possible to get flights using regular MONSTR flights determination code.
        Need to search explicitly for headers, by seeking 128 bytes (header size),
        as data inside is multiple of 128

    """

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
        self.index = 0  # index of records beginning in bytes
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

        self.get_flight_starts()
        #self.extract_date_from_header()
        self.get_flight_intervals()
        self.get_dates_now()
        self.get_durations()


        self.dat.close()

    def get_flight_starts(self):
        while self.index < self.file_len:
            self.dat.seek(self.index)
            flight = self.dat.read(6)
            if flight == MONSTR:
                header = self.dat.read(122)
                check = self.check_header(header)
                if check:  # header is valid
                    self.flights_start.append(self.index)
                    self.headers.append(header)
                else:  # header is not valid
                    pass
            self.index += HEADER_SIZE

    def extract_date_from_header(self):
        for header in self.headers:
            #date_bytes = [32, 34, 36, 38, 40, 42]

            year = '20' + str(ord(header[32]))

            month = '0' + str(ord(header[34])) if \
                             len(str(ord(header[34]))) == 1 else \
                             str(ord(header[34]))

            day = '0' + str(ord(header[36])) if \
                             len(str(ord(header[36]))) == 1 else \
                             str(ord(header[36]))

            hour = '0' + str(ord(header[38])) if \
                             len(str(ord(header[38]))) == 1 else \
                             str(ord(header[38]))

            minute = '0' + str(ord(header[40])) if \
                             len(str(ord(header[40]))) == 1 else \
                             str(ord(header[40]))

            second = '0' + str(ord(header[42])) if \
                             len(str(ord(header[42]))) == 1 else \
                             str(ord(header[42]))

            start_date = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            self.start_date.append(start_date)
            year, month, day, hour, minute, second = self.str_date_repr(start_date)
            self.start_date_str_repr.append([year, month, day, hour, minute, second])

    def get_dates_now(self):
        """ get todays date and time in case in header this data is wrong (wrong calendar operation)"""
        for flight in self.flight_intervals:
            start_date = datetime.datetime.now()
            self.start_date.append(start_date)
            year, month, day, hour, minute, second = self.str_date_repr(start_date)
            self.start_date_str_repr.append([year, month, day, hour, minute, second])

    def get_flight_intervals(self):

        """ flight intervals may be found either by headers index
            or by checking for 'end pattern'
            different types have different end patterns

            - bur3 flight ends either by zeroes or by next header
              last flight ends either by zeroes or by file end """

        if self.info == "b737_4700" or self.info == "an74_bur3"\
                or self.info == "an74_bur3_analog":
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

    def str_date_repr(self, start_date):

        """ date in string format """

        year = start_date.strftime("%y")
        month = start_date.strftime("%m")
        day = start_date.strftime("%d")
        hour = start_date.strftime("%H")
        minute = start_date.strftime("%M")
        second = start_date.strftime("%S")
        return year, month, day, hour, minute, second
