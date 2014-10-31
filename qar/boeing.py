import os
import datetime
import time
from qarReader_prod_v2 import QARReader


class Boeing(object):

    """ This class ensures flights search and
    data integrity check obtained from Boeing 747-200"""

    def __init__(self, path):
        self.path = path
        self.data = open(self.path, 'rb')
        self.flight_len = os.stat(self.path).st_size
        #self.index = 524288  # index of records beginning in bytes
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.qar_type = "b747_qar"
        self.init_date = None
        self.durations = []
        self.bytes_counter = 0
        self.subframe_len = 128
        self.frame_len = 512
        self.frame_duration = 4  # sec
        self.end_flag = False
        self.record_end_index = False
        #self.sw_one = "4702"
        #self.sw_two = "b805"
        #self.sw_three = "470a"
        #self.sw_four = "b80d"
        # decimal representation of syncwords
        self.sw_one = ["71", "2"]
        self.sw_two = ["184", "5"]
        self.sw_three = ["71", "10"]
        self.sw_four = ["184", "13"]
        self.find_flights()
        #for no we have no data -> create list of None for each date
        date = datetime.datetime(int(2014), int(1), int(1), int(0), int(0), int(0))
        self.start_date = [date] * len(self.flights_start)
        self.end_date = [date] * len(self.flights_start)
        self.get_flight_intervals()
        self.get_durations()
        #self.data.close()

    def find_flights(self):
        while not self.end_flag:
            start = self.get_flight_start()
            while start is True:
                check = self.check_frame()
                if check is True:
                    pass
                else:
                    start = False
                    self.bytes_counter += self.frame_len - self.subframe_len

    def get_flight_start(self):
        while not self.end_flag:
            byte_one = self.data.read(1)
            p12 = self.data.tell()
            byte_two = self.data.read(1)
            if byte_one == "" or byte_two == "":
                self.end_flag = True
                break
            p13 = self.data.tell()
            next_two_bytes = [str(ord(byte_one)), str(ord(byte_two))]
            self.bytes_counter += 2
            if next_two_bytes == self.sw_one:
                self.bytes_counter -= 2
                flight_start = self.bytes_counter
                self.data.seek(-2, 1)
                check = self.check_frame()
                if check is True:
                    self.flights_start.append(flight_start)
                    #print(flight_start)
                    self.record_end_index = True
                    return True
            else:
                self.data.seek(-1, 1)
                p11 = self.data.tell()
                self.bytes_counter -= 1
            if self.record_end_index is True:
                self.flights_end.append(self.bytes_counter)
                self.record_end_index = False


    def check_frame(self):
        check_sw_two = self.read_syncword()
        check_sw_three = self.read_syncword()
        check_sw_four = self.read_syncword()
        if (check_sw_two == self.sw_two and check_sw_three == self.sw_three
            and check_sw_four == self.sw_four):
            self.bytes_counter += self.frame_len
            self.data.seek(self.subframe_len, 1)
            p3 = self.data.tell()
            #self.bytes_counter += self.subframe_len
            return True

    def read_syncword(self):
        self.data.seek(self.subframe_len, 1)
        sw_ord = []
        sw = self.data.read(2)
        for each in sw:
            sw_ord.append(str(ord(each)))
        self.data.seek(-2, 1)
        p2 = self.data.tell()
        return sw_ord

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start):
            start = self.flights_start[i]
            try:
                end = self.flights_end[i]
            except IndexError:
                end = self.flight_len
            self.flight_intervals.append((start, end))
            i += 1
        '''
        i = 0
        for each in self.flights_start:
            try:
                self.flight_intervals.append((self.flights_start[i], self.flights_start[i + 1]))
            except IndexError:
                self.flight_intervals.append((self.flights_start[i], self.flight_len)) # last byte in file
            i += 1'''

    def get_durations(self):
        for each in self.flight_intervals:
            # get amount of bytes in flight, delete on frame length -> number of frames
            # multiply by 4 sec -> duration of each frame
            flight_duration = ((each[1] - each[0]) / self.frame_len) * self.frame_duration
            self.durations.append(flight_duration)