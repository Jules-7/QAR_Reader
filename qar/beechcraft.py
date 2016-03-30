#-*-coding: utf-8-*-

import os
import datetime
import struct
import win32api
from source_data import QAR_TYPES


class Beechcraft(object):

    """
        B300 beechcraft

        1. frames starts with syncword 04 11
        2. if not 04 11 - end of a flight
        3. no time no date
    """

    def __init__(self, path, chosen_acft_type, progress_bar):
        self.path = path
        self.dat = open(path, "rb")
        self.file_len = os.stat(path).st_size
        self.chosen_acft_type = chosen_acft_type
        self.qar_type = QAR_TYPES[self.chosen_acft_type][1]
        self.start = False
        self.end = False
        self.syncword = [4, 17]  # 04 11 in hex
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.durations = []
        self.start_date = []
        self.end_date = []
        self.flights_ids = []
        self.bytes_counter = 0
        self.end_flag = None
        self.frame_size = QAR_TYPES[self.chosen_acft_type][2]  # byte
        #print self.frame_size
        self.frame_duration = QAR_TYPES[self.chosen_acft_type][3]  # sec
        self.progress_bar = progress_bar

        self.find_flights()
        self.progress_bar.SetValue(25)

        self.get_flight_intervals()
        self.progress_bar.SetValue(45)

        self.get_durations()
        self.progress_bar.SetValue(65)

        self.get_date_time()
        self.progress_bar.SetValue(85)

    def find_flights(self):
        """
        Data in flights are all in frames
        Nothing need to be done with frames
        Just search for syncword and append
        every frame starts with 04 11 (hex) - 4 17 (dec)
        every frame 130 byte
        as soon as next frame doesnt start with syncword - end of a flight
        """
        while self.bytes_counter < self.file_len and not self.end_flag:
            pos = self.dat.tell()
            to_check = self.dat.read(2)
            try:
                check_syncword = [ord(each) for each in to_check]
            except ValueError:
                # no more data
                self.end_flag = True
                break
            # self.bytes_counter += 2
            if check_syncword == self.syncword:
                if not self.start:
                    self.start = True
                    self.end = False
                    self.flights_start.append(self.bytes_counter)
                self.bytes_counter += self.frame_size
                self.dat.seek(self.frame_size - 2, 1)
            else:
                if not self.end:
                    # frame diesnt start with syncword - means its the end of a flight
                    self.start = False
                    self.end = True
                    self.flights_end.append(self.bytes_counter)
                self.bytes_counter += self.frame_size
                self.dat.seek(self.frame_size - 2, 1)

    def get_flight_intervals(self):
        i = 0
        for each in self.flights_start:
            self.flight_intervals.append((self.flights_start[i], self.flights_end[i]))
            i += 1

    def get_date_time(self):
        for each in self.flight_intervals:
            date = datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0, second=0)
            self.start_date.append(date)
            self.end_date.append(date)

    def get_durations(self):
        for each in self.flight_intervals:
            start = each[0]
            end = each[1]
            duration = ((end - start) / self.frame_size) * self.frame_duration
            self.durations.append(duration)