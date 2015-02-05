import os
import datetime
from processing import PrepareData


class Boeing(object):

    """ Common attributes and methods for Boeing flights to be displayed """

    def __init__(self, path, acft, qar=None):
        self.path = path
        self.data = None
        self.data_len = None
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.acft = acft
        self.qar_type = qar
        self.init_date = None
        self.durations = []
        self.bytes_counter = 0
        self.subframe_len = None
        self.frame_len = None
        self.frame_duration = None  # sec
        self.end_flag = False
        self.record_end_index = False
        self.start_date = []
        self.end_date = []

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start):
            start = self.flights_start[i]
            try:
                end = self.flights_end[i]
            except IndexError:
                end = self.data_len
            self.flight_intervals.append((start, end))
            i += 1

    def get_durations(self):
        for each in self.flight_intervals:
            # get amount of bytes in flight,
            # delete on frame length -> number of frames
            # multiply by 4 sec -> duration of each frame
            flight_duration = ((each[1] - each[0]) /
                               self.frame_len) * self.frame_duration
            self.durations.append(flight_duration)

    def get_flight_ends(self):
        """ end of each flight
        gets as start date + flight duration"""
        i = 0
        for each in self.start_date:
            duration = self.durations[i]  # seconds
            #print(duration)
            end_date = each + datetime.timedelta(seconds=duration)
            self.end_date.append(end_date)
            i += 1


class B737(PrepareData):

    """ B737 DFDR 980
        scheme search, frames check, data record """

    def __init__(self, tmp_file_name, param_file_name, frame, subframe,
                 progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name, param_file_name, frame,
                             subframe, progress_bar, path_to_save, flag)
        self.progress_bar.Show()
        self.qar_type = flag
        self.progress_bar.SetValue(5)
        source = open(tmp_file_name, "rb")
        # just created tmp parametric file
        self.source_file = source.read()
        # size of tmp parametric file
        self.param_file_end = len(self.source_file)
        self.progress_bar.SetValue(25)
        #-- find mix type scheme -
        self.scheme_search()
        self.progress_bar.SetValue(45)
        self.record_data()
        self.progress_bar.SetValue(85)
        source.close()
        self.progress_bar.SetValue(95)


class B747(Boeing):

    """ Boeing 747-200
        Search flights and data integrity check """

    def __init__(self, path, acft, qar):
        Boeing.__init__(self, path, acft, qar)
        self.data = open(self.path, 'rb')
        self.data_len = os.stat(self.path).st_size
        #self.qar_type = "b747_qar"
        self.init_date = None
        self.subframe_len = 128
        self.frame_len = 512
        self.frame_duration = 4  # sec
        self.end_flag = False
        self.record_end_index = False
        # decimal representation of syncwords
        # check of each byte separately,
        # as other bytes can give the combination = 712 (for example)
        self.sw_one = ["71", "2"]     # hex -> "4702"
        self.sw_two = ["184", "5"]    # hex -> "b805"
        self.sw_three = ["71", "10"]  # hex -> "470a"
        self.sw_four = ["184", "13"]  # hex -> "b80d"

        self.find_flights()
        self.get_flight_intervals()
        self.get_durations()
        self.data.close()
        self.data = open(self.path, 'rb')
        self.get_time()
        self.get_flight_ends()

    def find_flights(self):
        """ find all flights
                    in B747 - all the frames are good
                    if there is no syncword in the next frame -
                    it is an indication of the flight end"""
        while not self.end_flag:
            start = self.get_flight_start()
            while start:  # if start is found
                check = self.check_frame()  # check frame
                if check:  # if it is correct
                    pass  # don`t do anything
                else:
                    start = False  # means that flight has ended
                    #self.bytes_counter += self.frame_len - self.subframe_len

    def get_flight_start(self):
        while not self.end_flag:
            byte_one = self.data.read(1)
            #p12 = self.data.tell()
            byte_two = self.data.read(1)
            if byte_one == "" or byte_two == "":
                self.end_flag = True
                break
            #p13 = self.data.tell()
            next_two_bytes = [str(ord(byte_one)), str(ord(byte_two))]
            self.bytes_counter += 2
            if next_two_bytes == self.sw_one:
                self.bytes_counter -= 2
                flight_start = self.bytes_counter
                self.data.seek(-2, 1)
                check = self.check_frame()
                if check:
                    self.flights_start.append(flight_start)
                    #print(flight_start)
                    self.record_end_index = True
                    return True
            else:
                self.data.seek(-1, 1)
                p11 = self.data.tell()
                #self.bytes_counter = p11
                self.bytes_counter -= 1
            if self.record_end_index:
                self.flights_end.append(self.bytes_counter)
                # important value -> ensures same value of
                # actual index in file and bytes_counter
                self.bytes_counter = p11
                self.record_end_index = False

    def check_frame(self):
        """ check if there is a next frame """
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
        """ read syncword and convert to str format"""
        self.data.seek(self.subframe_len, 1)
        sw_ord = []
        sw = self.data.read(2)
        for each in sw:
            sw_ord.append(str(ord(each)))
        self.data.seek(-2, 1)
        p2 = self.data.tell()
        return sw_ord

    def get_time(self):
        """ At the beginning of flight - data loss or corruption may occur
        In order to get correct time -> take time from the middle of a flight
        and calculate its start and end using amount of frames
        - minutes are recorded at 1st subframe only at 72 and 73 bytes
        - hours are recorded at 3d subframe only at 72"""
        i = 1
        for each in self.flight_intervals:
            frames_in_flight = (each[1] - each[0]) / self.frame_len
            # amount of frames in half flight
            half_flight_frames = frames_in_flight / 2
            # index of half flight
            half_flight_index = each[0] + half_flight_frames * self.frame_len

            #--------- subframe 1 byte 72 and 73 (36 channel)
            minutes_index = half_flight_index + 36 * 2
            self.data.seek(minutes_index, 0)
            minutes = [self.data.read(1), self.data.read(1)]

            # --- 73d bytes comes first, than 72d byte
            m_ord = [ord(minutes[1]), ord(minutes[0])]
            m_bin = [bin(m_ord[0]), bin(m_ord[1])]
            min_binary_str = ""
            for each in m_bin:
                min_binary_str += ((str(each))[2:]).rjust(8, "0")
            min_digit_one = int(min_binary_str[6:10], 2)
            min_digit_two = int(min_binary_str[12:], 2)

            minutes_checked = self.check_minutes(min_digit_one, min_digit_two)

            #--------- subframe 3 byte 72 (36 channel) ---------
            hours_index = half_flight_index + self.subframe_len * 2 + 36 * 2
            self.data.seek(hours_index, 0)
            hours = self.data.read(1)
            h_ord = ord(hours)
            h_bin = bin(h_ord)
            h_binary_str = ((str(h_bin))[2:]).rjust(8, "0")

            hour_digit_one = int(h_binary_str[:2], 2)
            hour_digit_two = int(h_binary_str[4:], 2)
            hours_checked = self.check_hours(hour_digit_one, hour_digit_two)

            #for no we have no data -> create list of None for each date
            middle_date = datetime.datetime(year=2015,
                                            month=1,
                                            day=1,
                                            hour=hours_checked,
                                            minute=minutes_checked,
                                            second=0)
            # seconds first half of flight
            duration = half_flight_frames * self.frame_duration
            start_date = middle_date - datetime.timedelta(seconds=duration)
            self.start_date.append(start_date)
            i += 1

    def check_minutes(self, digit_one, digit_two):
        """ check minutes to be in valid range"""
        digit_one_corrected = None
        digit_two_corrected = None
        if digit_one > 5:
            digit_one_corrected = 5
        if digit_two >= 10:
            digit_two_corrected = 9
        if digit_one_corrected:
            one = digit_one_corrected
        else:
            one = digit_one
        if digit_two_corrected:
            two = digit_two_corrected
        else:
            two = digit_two
        return int("%s%s" % (one, two))

    def check_hours(self, digit_one, digit_two):
        """ check hours to be in valid range"""
        digit_one_corrected = None
        digit_two_corrected = None
        if digit_one > 2:
            digit_one_corrected = 2
        if digit_one_corrected:
            digit_one = digit_one_corrected
        if digit_one < 2 and digit_two >= 10:
            digit_two_corrected = 9
        elif digit_one == 2 and digit_two >= 4:
            digit_two_corrected = 3
        if digit_one_corrected:
            one = digit_one_corrected
        else:
            one = digit_one
        if digit_two_corrected:
            two = digit_two_corrected
        else:
            two = digit_two
        return int("%s%s" % (one, two))


class Boeing737DFDR980(Boeing):

    """ Boeing 737 DFDR 980
        Find flights to display"""

    def __init__(self, path, acft, fdr):
        Boeing.__init__(self, path, acft, fdr)
        self.path = path
        self.end_pattern = [0] * 20
        self.start_pattern = [255] * 20
        self.data = open(self.path, "rb").read()
        self.data_len = os.stat(self.path).st_size
        #self.acft = acft
        #self.qar_type = fdr
        self.start_index = None
        self.init_date = None
        self.end_flag = False
        self.data_start = None
        self.record_end_index = False
        self.subframe_len = 96
        self.frame_len = 384
        self.frame_duration = 5  # sec

        self.find_start()
        #self.find_flights()
        #self.correct_flights_starts()
        self.get_flight_intervals()
        self.get_durations()
        self.get_date_time()

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
        #c = 0
        #for each in self.data[self.bytes_counter:]:
            #if ord(each) == 0:
                #c += 1
            #else:
                #c = 0
            #self.bytes_counter += 1
            #if c == 20:
                #self.flights_start.append(self.bytes_counter)
                #break  # found first set of 00 00 00 ...

    def find_flights(self):
        """ find all flights starts """
        while self.bytes_counter < len(self.data):
            # start looking from current position
            self.find_flight_start(self.data[self.bytes_counter:])

    def find_flight_start(self, data_range):
        i = 0
        for each in data_range:
            if ord(each) == 0:
                i += 1
            else:
                i = 0
            self.bytes_counter += 1
            if i == 20:
                self.flights_start.append(self.bytes_counter)
                # ensure cases when zeroes = 40 and more
                # increase position to pass zeroes
                self.bytes_counter += 40
                return

    def correct_flights_starts(self):
        """ At the end of a record plenty zeroes may be present (up to 200).
            In such case, algorithm of flight end and start detection
            will catch them and include as flights beginnings.
            If this is a case -> difference between flights start
            will be about 60 bytes (according to current algorithm).
            That`s why check of differences between starts
            must be performed """
        #i = 0
        #while i < len(self.flights_start)-1:
            #if self.flights_start[i+1] - self.flights_start[i] <= 40000:
                #del self.flights_start[i+1]
            #else:
                #i += 1
        #if self.data_len - self.flights_start[-1] <= self.frame_len:
            #del self.flights_start[-1]
        # at switching to engine generator - power surge appears
        # it cases appearance of bunch of zeroes after that
        # thus causing absence of data (zeroes) after right engine is started
        # and after its turn off
        # in order to count this case ->
        # first: if difference between two starts is less or equal 80000 Bytes ->
        # do not take the second index as new flight start
        # the small parts (less than 10 min) contain engines turn off and on
        # second: include small parts both - before and after flight main part
        # thus resulting in flight containing engines turn off from previous flight
        # at record beginning and engines turn on from next flight at record
        # ending
        self.starts = []
        self.ends = []
        i = 0
        while i <= len(self.flights_start)-1:
            try:
                if self.flights_start[i+1] - self.flights_start[i] <= 80000:
                    self.starts.append(self.flights_start[i])
                    try:
                        if self.flights_start[i+3] - self.flights_start[i+2] <= 80000:
                            self.ends.append(self.flights_start[i+3])
                        else:
                            self.ends.append(self.flights_start[i+2])
                    except IndexError:  # no further flights
                        self.ends.append(self.data_len)
                    i += 2
                else:
                    self.starts.append(self.flights_start[i])
                    self.ends.append(self.flights_start[i+1])
                    i += 1
                self.flights_start = self.starts
            except IndexError:  # only one flight start
                self.starts.append(self.data_start)
                self.ends.append(self.data_len)
                self.flights_start = self.starts
                #print self.starts, self.ends
                break

    def get_flight_intervals(self):
        #i = 0
        #while i < len(self.starts):
            #self.flight_intervals.append((self.starts[i], self.ends[i]))
            #i += 1
        #print(self.flight_intervals)
        #take all flights as a whole record from data start till data end
        self.flight_intervals.append((self.flights_start[0], self.data_len))

    def get_date_time(self):
        date = datetime.datetime.now()
        for each in self.flight_intervals:
            self.start_date.append(date)
            self.end_date.append(date)