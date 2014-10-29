import os
import datetime


class Bur(object):

    def __init__(self, path):
        self.path = path
        self.dat = open(path, "rb")
        self.file_len = os.stat(path).st_size
        self.qar_type = u"Bur-92"
        self.start = True
        self.flights_start = [0]
        self.flights_end = []
        self.flight_intervals = []
        self.durations = []
        self.bytes_counter = 0
        self.frame = 512  # byte
        self.frame_duration = 1  # sex
        self.end_check = [255] * 4
        self.end_pattern = [255] * self.frame
        self.get_flights()
        #print(self.flights_start)

        self.get_flight_intervals()
        self.get_durations()
        date = datetime.datetime(int(2014), int(1), int(1), int(0), int(0), int(0))
        self.start_date = [date] * len(self.flights_start)
        self.end_date = [date] * len(self.flights_start)

    def get_flights(self):
        while self.bytes_counter < self.file_len - self.frame:
            if self.start is True:
                p = self.dat.tell()
                check_word = [ord(each) for each in self.dat.read(4)]
                if check_word == self.end_check:
                    self.dat.seek(-4, 1)
                    check_end = [ord(each) for each in self.dat.read(self.frame)]
                    self.bytes_counter += self.frame
                    if check_end == self.end_pattern:
                        self.flights_end.append(self.bytes_counter - self.frame)
                        self.start = False
                        self.bytes_counter = self.dat.tell()
                else:
                    self.dat.seek(self.frame - 4, 1)
                    self.bytes_counter += self.frame
            else:
                check_word = [ord(each) for each in self.dat.read(4)]
                if check_word != self.end_check:
                    self.flights_start.append(self.bytes_counter)
                    self.start = True
                    self.dat.seek(self.frame - 4, 1)
                    self.bytes_counter += self.frame
                else:
                    self.dat.seek(self.frame - 4, 1)
                    self.bytes_counter += self.frame

    def get_flight_intervals(self):
        if (len(self.flights_start)) > (len(self.flights_end)):
            self.flights_end.append(self.file_len)
        i = 0
        while i < len(self.flights_start):
            self.flight_intervals.append((self.flights_start[i], self.flights_end[i]))
            i += 1

    def get_durations(self):
        for each in self.flight_intervals:
            duration = ((each[1] - each[0]) / self.frame) * self.frame_duration
            self.durations.append(duration)
