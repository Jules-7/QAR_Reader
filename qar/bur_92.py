import os
import datetime


class Bur(object):

    def __init__(self, path):
        self.path = path
        self.dat = open(path, "rb")
        # in order to avoid header and starting "noises"
        self.dat.seek(12800, 0)
        self.file_len = os.stat(path).st_size
        self.qar_type = "BUR-92"
        self.start = False
        self.syncword_one = [0, 0]
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.durations = []
        self.start_date = []
        self.end_date = []
        # in order to avoid header and starting "noises"
        self.bytes_counter = 12800
        self.frame_size = 512  # byte
        self.frame_duration = 1  # sec
        self.end_check = [255] * 4
        self.end_pattern = [255] * self.frame_size
        self.find_start()
        self.get_flights()
        self.get_flight_intervals()
        self.get_durations()
        self.get_date_time()
        self.get_flight_ends()

    def get_flights(self):
        while self.bytes_counter < self.file_len - self.frame_size:
            if self.start:
                #p = self.dat.tell()
                check_word = [ord(each) for each in self.dat.read(4)]
                if check_word == self.end_check:
                    self.dat.seek(-4, 1)
                    check_end = [ord(each) for each in
                                 self.dat.read(self.frame_size)]
                    self.bytes_counter += self.frame_size
                    if check_end == self.end_pattern:
                        self.flights_end.append(self.bytes_counter -
                                                self.frame_size)
                        self.start = False
                        self.bytes_counter = self.dat.tell()
                else:
                    self.dat.seek(self.frame_size - 4, 1)
                    self.bytes_counter += self.frame_size
            else:
                check_word = [ord(each) for each in self.dat.read(4)]
                if check_word != self.end_check:
                    self.flights_start.append(self.bytes_counter)
                    self.start = True
                    self.dat.seek(self.frame_size - 4, 1)
                    self.bytes_counter += self.frame_size
                else:
                    self.dat.seek(self.frame_size - 4, 1)
                    self.bytes_counter += self.frame_size

    def find_start(self):
        while not self.start:
            byte_one = self.dat.read(1)
            byte_two = self.dat.read(1)
            syncword = [ord(byte_one), ord(byte_two)]
            #p1 = self.dat.tell()
            if syncword == self.syncword_one:
                self.start = True
                self.flights_start.append(self.bytes_counter)
                self.dat.seek(-2, 1)
            else:
                self.dat.seek(-1, 1)
                self.bytes_counter += 1

    def get_flight_intervals(self):
        """ according to end pattern """
        if (len(self.flights_start)) > (len(self.flights_end)):
            self.flights_end.append(self.file_len)
        i = 0
        while i < len(self.flights_start):
            try:
                self.flight_intervals.append((self.flights_start[i],
                                              self.flights_end[i]))
            except IndexError:
                self.flight_intervals.append((self.flights_start[i],
                                              self.file_len))
            i += 1

    def get_durations(self):
        i = 0
        while i < len(self.flight_intervals):
            interval = self.flight_intervals[i]
        #for each in self.flight_intervals:
            duration = ((interval[1] - interval[0]) / self.frame_size) * \
                        self.frame_duration
            # if flight is of frame size - it`s not flight
            if duration == 1:
                self.flight_intervals.remove(interval)
                del self.flights_start[i]
                del self.flights_end[i]
            else:
                self.durations.append(duration)
                i += 1

    def get_date_time(self):
        """ time and date are recorded at the beginning of each frame
        (each 512 starting with 00 00 - 1st and 2d bytes):
        - seconds at 3-4 B
        - minutes at 5-6 B
        - hours at 7-8 B
        - year is recorded only at frame where seconds == 3
        - month is recorded only at frame where seconds == 4
        - day is recorded only at frame where seconds == 5
        In order to get stable time -> find 'middle flight time'
        and then get start and end flight time
        knowing amount of frames in flight"""
        datetime_reference_table = {}
        for each in self.flight_intervals:
            # amount of frames in flight
            frames_in_flight = (each[1] - each[0]) / self.frame_size
            frame_half_flight = frames_in_flight / 2  # amount of frames in half
            # byte
            middle_flight_index = each[0] + frame_half_flight * self.frame_size
            self.dat.seek(middle_flight_index, 0)
            # one minute is 60 frames
            seconds_N = 0
            while seconds_N < 60:
                one_frame = self.dat.read(self.frame_size)
                pp2 = self.dat.tell
                sec = self.convert_data(one_frame[2:4])
                sec_ord = self.convert_in_ord(sec)
                if sec_ord == 3:  # at 3d second year is recorded as date channel
                    minute = self.convert_data(one_frame[4:6])
                    hour = self.convert_data(one_frame[6:8])
                    date = self.convert_data(one_frame[8:])
                    datetime_reference_table[sec_ord] = [minute, hour, date]
                elif sec_ord == 4:  # at 4th second month is recorded as date channel
                    minute = self.convert_data(one_frame[4:6])
                    hour = self.convert_data(one_frame[6:8])
                    date = self.convert_data(one_frame[8:])
                    datetime_reference_table[sec_ord] = [minute, hour, date]
                elif sec_ord == 5:  # at 5th second day is recorded as date channel
                    minute = self.convert_data(one_frame[4:6])
                    hour = self.convert_data(one_frame[6:8])
                    date = self.convert_data(one_frame[8:])
                    datetime_reference_table[sec_ord] = [minute, hour, date]
                    break
                seconds_N += 1
            middle_flight_date_time = self.get_middle_flight_date(datetime_reference_table)
            duration = frame_half_flight * self.frame_duration  # sec first half of flight
            start_date = middle_flight_date_time - datetime.timedelta(seconds=duration)
            self.start_date.append(start_date)

    def convert_data(self, data):
        """ Perform change by place bytes and obtain string binary representation """
        switch_data = [(str(bin(ord(data[1])))[2:]).rjust(8, "0"),
                       (str(bin(ord(data[0])))[2:]).rjust(8, "0")]
        data_str = "".join('1' if x == '0' else '0' for x in (switch_data[0] +
                                                              switch_data[1]))
        return data_str

    def convert_in_ord(self, data):
        """ convert to ordinary representation"""
        first_digit = int(data[8:12], 2)
        second_digit = int(data[12:], 2)
        data_ord = int(str(first_digit) + str(second_digit))
        return data_ord

    def get_middle_flight_date(self, date_time):
        year = None
        month = None
        day = None
        hours = None
        minutes = None
        sec = None
        for key, value in date_time.iteritems():
            if key == 3:  # get minutes, hour and year
                sec = key
                minutes = self.convert_in_ord(value[0])
                hours = self.convert_in_ord(value[1])
                year = int("20" + str(self.convert_in_ord(value[2])))
            elif key == 4:
                month = self.convert_in_ord(value[2])
            elif key == 5:
                day = self.convert_in_ord(value[2])
        if minutes < 0:
            minutes = 0
        elif minutes > 59:
            minutes = 59
        middle_date_time = datetime.datetime(year=year, month=month, day=day,
                                             hour=hours, minute=minutes, second=sec)
        return middle_date_time

    def get_flight_ends(self):
        i = 0
        for each in self.start_date:
            end_date = each + datetime.timedelta(seconds=self.durations[i])
            self.end_date.append(end_date)
            i += 1