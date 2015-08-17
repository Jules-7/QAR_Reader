import os
import datetime
from processing import PrepareData
from source_data import QAR_TYPES, ARINC_DIRECT


class Boeing(object):

    """ Common attributes and methods for Boeing flights
        to be found and displayed """

    def __init__(self, path, flag):
        self.path = path
        self.data = None
        self.data_len = None
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.acft = QAR_TYPES[flag][0]
        self.qar_type = QAR_TYPES[flag][1]
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
            # depends on frame length -> number of frames
            # multiply by 4 sec -> duration of each frame
            flight_duration = ((each[1] - each[0]) /
                               self.frame_len) * self.frame_duration
            self.durations.append(flight_duration)

    def get_flight_ends(self):
        """ end of each flight
            equals to -> start date + flight duration"""
        i = 0
        for each in self.start_date:
            duration = self.durations[i]  # seconds
            end_date = each + datetime.timedelta(seconds=duration)
            self.end_date.append(end_date)
            i += 1


class B737(PrepareData):

    """ B737 DFDR 980
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

        # find mix type scheme
        self.scheme_search()
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)

        source.close()
        self.progress_bar.SetValue(100)


class B747Series200(Boeing):

    """ Boeing 747-200
        Search flights and data integrity check """

    def __init__(self, path, flag):
        Boeing.__init__(self, path, flag)
        self.data = open(self.path, 'rb')
        self.data_len = os.stat(self.path).st_size
        self.init_date = None
        self.frame_len = QAR_TYPES[flag][2]
        self.subframe_len = self.frame_len / 4
        self.frame_duration = QAR_TYPES[flag][3]  # sec
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

    def get_flight_start(self):
        while not self.end_flag:
            byte_one = self.data.read(1)
            byte_two = self.data.read(1)
            if byte_one == "" or byte_two == "":
                self.end_flag = True
                break
            next_two_bytes = [str(ord(byte_one)), str(ord(byte_two))]
            self.bytes_counter += 2
            if next_two_bytes == self.sw_one:
                self.bytes_counter -= 2
                flight_start = self.bytes_counter
                self.data.seek(-2, 1)
                check = self.check_frame()
                if check:
                    self.flights_start.append(flight_start)
                    self.record_end_index = True
                    return True
            else:
                self.data.seek(-1, 1)
                current_pos = self.data.tell()
                self.bytes_counter -= 1
            if self.record_end_index:
                self.flights_end.append(self.bytes_counter)
                # important value -> ensures same value of
                # actual index in file and bytes_counter
                self.bytes_counter = current_pos
                self.record_end_index = False

    def check_frame(self):
        """ check if there is a next frame """
        check_sw_two = self.read_syncword()
        check_sw_three = self.read_syncword()
        check_sw_four = self.read_syncword()
        if check_sw_two == self.sw_two and check_sw_three == self.sw_three and check_sw_four == self.sw_four:
            self.bytes_counter += self.frame_len
            self.data.seek(self.subframe_len, 1)

            return True

    def read_syncword(self):
        """ read syncword and convert to str format"""
        self.data.seek(self.subframe_len, 1)
        sw_ord = []
        sw = self.data.read(2)
        for each in sw:
            sw_ord.append(str(ord(each)))
        self.data.seek(-2, 1)
        return sw_ord

    def get_time(self):
        """ At the beginning of flight - data loss or corruption may occur
        In order to get correct time -> take time from the middle of a flight
        and calculate its start and end using amount of frames
        - minutes are recorded at 1st subframe only at 72 and 73 bytes
        - hours are recorded at 3d subframe only at 72"""
        i = 1
        for flight in self.flight_intervals:
            frames_in_flight = (flight[1] - flight[0]) / self.frame_len
            # amount of frames in half flight
            half_flight_frames = frames_in_flight / 2
            # index of half flight
            half_flight_index = flight[0] + half_flight_frames * self.frame_len

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

            # for now we have no data -> create list of None for each date
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


class B747Series300(Boeing):
    """
        B747-300 QAR 4700

        Flights search

        1. Find 00 04 (hex)
        2. Find next 00 04 after 512 B. If so - its a start of a flight and go from here
        3. Take flight start from the first 00 04 - 00 04 frame.
        4. Flight end pattern is 2 bytes of 00
        5. To find the rest of flights - repeat steps 2-4

    """

    def __init__(self, path, flag):
        super(B747Series300, self).__init__(path, flag)
        self.data = open(self.path, 'rb')
        self.data_len = os.stat(self.path).st_size
        self.init_date = None
        self.frame_len = 512
        self.subframe_len = self.frame_len / 4
        self.frame_duration = 4  # sec
        self.end_flag = False
        self.record_end_index = False
        self.flight_end_pattern = ["0"] * 16
        self.sw_one = ["0", "4"]     # hex -> "0004"
        self.current_pos = 0
        self.count_empty_data = 0

        self.find_flights()
        self.get_flight_intervals()
        self.get_durations()
        self.data.close()
        self.get_time()
        self.get_flight_ends()

    def find_flights(self):
        """ find 0004, then next 0004 in 512 B - its a flight start
            flight end pattern - 2 bytes of 00 (actually its almost a frame of 00)
        """
        while not self.end_flag:
            self.current_pos = self.data.tell()
            start = self.get_flight_start()
            self.flights_start.append(start)
            end = self.get_flight_end()
            self.flights_end.append(end)

    def get_flight_start(self):
        while not self.end_flag:
            byte_one = self.data.read(1)
            self.current_pos = self.data.tell()
            byte_two = self.data.read(1)
            if byte_one == "" or byte_two == "":
                self.end_flag = True
                return
            try:  # after the last flight there might be a lot of data
                if self.bytes_counter - self.flights_end[-1] > self.frame_len * 10:
                    self.end_flag = True
                    return
            except IndexError:  # there is no any record in flights end
                pass
            self.current_pos = self.data.tell()
            next_two_bytes = [str(ord(byte_one)), str(ord(byte_two))]
            self.bytes_counter += 2
            if next_two_bytes == self.sw_one:
                self.bytes_counter -= 2
                self.current_pos = self.data.tell()
                self.data.seek(-2, 1)
                self.current_pos = self.data.tell()
                check = self.check_frame()
                self.current_pos = self.data.tell()
                if check:
                    self.current_pos = self.data.tell()
                    self.data.seek(-self.frame_len, 1)
                    return self.bytes_counter
                else:
                    self.data.seek(-(self.frame_len - 2), 1)
                    self.bytes_counter += 2
                    self.current_pos = self.data.tell()
            else:
                self.data.seek(-1, 1)
                self.current_pos = self.data.tell()
                self.bytes_counter -= 1

    def get_flight_end(self):
        self.current_pos = self.data.tell()
        counter = 0
        while not self.end_flag:
            if self.bytes_counter >= self.data_len:
                self.end_flag = True
                return self.data_len
            next_byte = self.data.read(1)
            self.current_pos = self.data.tell()
            if next_byte == "":
                self.end_flag = True
                return self.bytes_counter
            next_byte_value = str(ord(next_byte))
            if next_byte_value == "0":
                counter += 1
            else:
                counter = 0
            self.bytes_counter += 1
            self.current_pos = self.data.tell()
            if counter == len(self.flight_end_pattern):
                self.current_pos = self.data.tell()
                return self.bytes_counter

    def check_frame(self):
        """ check if there is a next frame """
        self.current_pos = self.data.tell()
        check_next_sw = self.read_syncword()
        self.current_pos = self.data.tell()
        if check_next_sw == self.sw_one:
            self.bytes_counter += self.frame_len
            self.data.seek(self.frame_len, 1)
            self.current_pos = self.data.tell()
            return True
        else:
            self.current_pos = self.data.tell()

    def read_syncword(self):
        """ read syncword and convert to str format"""
        self.data.seek(self.frame_len, 1)
        self.current_pos = self.data.tell()
        sw_ord = []
        sw = self.data.read(2)
        for each in sw:
            sw_ord.append(str(ord(each)))
        self.data.seek(-2, 1)
        self.current_pos = self.data.tell()
        return sw_ord

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start)-1:
            start = self.flights_start[i]
            end = self.flights_end[i]
            self.flight_intervals.append((start, end))
            i += 1

    def get_time(self):
        for flight in self.flight_intervals:
            start_date = datetime.datetime.now()
            self.start_date.append(start_date)


class B747Series300Process(PrepareData):

    """ B747 300 4700
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

        # find mix type scheme
        self.scheme_search()
        # print self.mix_type
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)

        source.close()
        self.progress_bar.SetValue(100)


class Boeing737DFDR980(Boeing):
    """ Boeing 737 DFDR 980
        Find flights to display"""
    sw_one = ARINC_DIRECT[1]
    sw_two = ARINC_DIRECT[2]

    def __init__(self, path, flag):
        Boeing.__init__(self, path, flag)
        self.path = path
        self.flag = flag # define fdr type
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
        if QAR_TYPES[self.flag][1] == "dfdr_980_BDV":
            pattern = 6
            for each in data_range:
                if ord(each) == 255:
                    i += 1
                else:
                    i = 0
                self.bytes_counter += 1
                if i == pattern:
                    self.append_start()
        else:
            pattern = 20
            for each in data_range:
                if ord(each) == 0:
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

    def correct_starts_at_beginning(self):
        """ At the end of a record plenty zeroes may be present (up to 200).
            In such case, algorithm of flight end and start detection
            will catch them and include as flights beginnings.
            If this is a case -> difference between flights start
            will be about 60 bytes (according to current algorithm).
            That`s why check of differences between starts
            must be performed

            small flight is appended at the beginning of the next big flight """
        for i, flight in enumerate(self.flights_start):
            try:
                if self.flights_start[i+1] - self.flights_start[i] <= 40000:
                    del self.flights_start[i+1]
            except IndexError:
                if self.data_len - self.flights_start[-1] <= self.frame_len:
                    del self.flights_start[-1]

    def correct_flights_starts(self):
        """ At the end of a record plenty zeroes may be present (up to 200).
            In such case, algorithm of flight end and start detection
            will catch them and include as flights beginnings.
            If this is a case -> difference between flights start
            will be about 60 bytes (according to current algorithm).
            That`s why check of differences between starts
            must be performed """
        # at switching to engine generator - power surge appears
        # it causes appearance of bunch of zeroes after that
        # thus causing absence of data (zeroes) after right engine is started
        # and after its turn off
        # in order to count this case ->
        # first: if difference between two starts is less or equal 40000 Bytes ->
        # do not take the second index as new flight start
        # the small parts (less than 10 min) contain engines turn off and on
        # second: include small parts both - before and after flight main part
        # thus resulting in flight containing engines turn off from previous flight
        # at record beginning and engines turn on from next flight at record
        # ending
        self.starts = []
        self.ends = []
        i = 0
        while i < len(self.flights_start) - 1:
            try:
                if self.flights_start[i+1] - self.flights_start[i] <= 40000:
                    self.starts.append(self.flights_start[i])
                    try:
                        if self.flights_start[i+3] - self.flights_start[i+2] <= 40000:
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
                #self.flights_start = self.starts
            except IndexError:  # only one flight start
                self.starts.append(self.data_start)
                self.ends.append(self.data_len)
                self.flights_start = self.starts
                break
        self.flights_start = self.starts

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

    def get_time(self):
        """ get date and time from flight first frame """
        self.bytes_counter = 0
        self.mix_type = None
        self.subframe_len = self.frame_len / 4  # in bytes
        source = open(self.path, "rb")
        self.source_end = self.frame_len * 4
        for i, each in enumerate(self.flights_start):
            source.seek(each)
            three_frames = self.frame_len * 4
            self.source_file = source.read(three_frames)
            self.find_mix_type()
            converted_frame = self.collect_converted()
            self.extract_time(converted_frame)

    def collect_converted(self):
        """ perform recording of valid frames only for
        further getting of date and time from it """
        converted_frame = []
        self.bytes_counter = 0
        while self.bytes_counter < self.source_end - 4:
            # cases when flight is too small less than 10 min
            if self.mix_type is None:
                print("didnt find syncword")

            elif self.mix_type % 2 == 1:
                #if syncword is found at 2d subword, it means that syncword
                #is at the end of list (2d, 3d bytes), so we shift two byes
                #and can use the same scheme but for first subword
                self.mix_type -= 1
                extract_syncword = [self.source_file[self.bytes_counter],
                                    self.source_file[self.bytes_counter + 1],
                                    self.source_file[self.bytes_counter + 2],
                                    self.source_file[self.bytes_counter + 3]]
                syncword_first = self.mix_words(extract_syncword)
                self.bytes_counter += 3
                # take the last two byte which contain syncword
                for each in syncword_first[2:]:
                    converted_frame.append(each)

                i = 0
                while i < self.frame_len - 3:
                    # read frame by 4 bytes, apply mix scheme to it and record
                    # to target file
                    # -1 byte_counter due to the fact the 12 bits words
                    words = [self.source_file[self.bytes_counter],
                             self.source_file[self.bytes_counter + 1],
                             self.source_file[self.bytes_counter + 2],
                             self.source_file[self.bytes_counter + 3]]
                    self.bytes_counter += 4
                    i += 4
                    words_mixed = self.mix_words(words)
                    self.bytes_counter -= 1
                    i -= 1
                    # take the last two byte which contain syncword
                    for each in words_mixed:
                        converted_frame.append(each)

                last_bytes = [self.source_file[self.bytes_counter],
                              self.source_file[self.bytes_counter + 1],
                              self.source_file[self.bytes_counter + 2],
                              self.source_file[self.bytes_counter + 3]]
                last_bytes_mixed = self.mix_words(last_bytes)
                # take the last two byte which contain syncword
                for each in last_bytes_mixed[:2]:
                    converted_frame.append(each)

                self.bytes_counter -= 2

            else:  # no need to change mix_type
                frame = self.source_file[self.bytes_counter:
                                         self.bytes_counter + self.frame_len + 4]
                if len(frame) < self.frame_len:  # end of data
                    break
                self.bytes_counter += self.frame_len
                self.bytes_counter -= 4
                try:
                    check_next_sw = [frame[(self.frame_len + 4) - 4],
                                     frame[(self.frame_len + 4) - 3],
                                     frame[(self.frame_len + 4) - 2],
                                     frame[(self.frame_len + 4) - 1]]
                except IndexError:  # end of data
                    break
                mixed_words = self.mix_syncword(check_next_sw)
                # perform syncword mixing according to mix scheme
                if mixed_words[self.mix_type] == self.sw_one:  # if its ok
                    i = 0
                    while i < self.frame_len:
                        next_words = [frame[i], frame[i + 1],
                                      frame[i + 2], frame[i + 3]]
                        i += 3
                        mix_next_words = self.mix_words(next_words)
                        for each in mix_next_words:
                            converted_frame.append(each)
                else:  # if its not a syncword -> search for it
                    self.bytes_counter -= self.frame_len
                    self.find_mix_type()
        return converted_frame

    def find_mix_type(self):
        """ Perform search of mix scheme type """
        found_sw = False  # indicator of found/not found syncword
        #---------four bytes, in which we search for syncword----
        try:
            search_bytes = [self.source_file[self.bytes_counter],
                            self.source_file[self.bytes_counter + 1],
                            self.source_file[self.bytes_counter + 2]]
        except IndexError:
            return
        self.bytes_counter += 3

        while not found_sw and self.bytes_counter < self.source_end:
            next_byte = self.source_file[self.bytes_counter]
            self.bytes_counter += 1
            search_bytes.append(next_byte)  # append fourth byte
            # send them to check for scheme
            mixed_words = self.mix_syncword(search_bytes)

            if mixed_words is None:
                break
            elif mixed_words == ["111111111111"] * 8:  # found end pattern
                self.bytes_counter = self.source_end
                break

            del search_bytes[0]  # remove first byte -> ensure shift by byte

            i = 0
            for word in mixed_words:
                if word == self.sw_one:
                    #----------------------------------------------------------
                    #print("found match")
                    #print(self.bytes_counter)
                    frame = self.source_file[self.bytes_counter:
                                             self.bytes_counter + self.frame_len]
                    self.bytes_counter += self.frame_len
                    try:
                        next_frame_search = [frame[self.frame_len - 4],
                                             frame[self.frame_len - 3],
                                             frame[self.frame_len - 2],
                                             frame[self.frame_len - 1]]
                    except IndexError:  # end of data
                        break
                    next_subframe_search = [frame[self.subframe_len - 4],
                                            frame[self.subframe_len - 3],
                                            frame[self.subframe_len - 2],
                                            frame[self.subframe_len - 1]]
                    frame_sw_variants = self.mix_syncword(next_frame_search)
                    subframe_sw_variants = self.mix_syncword(next_subframe_search)

                    if frame_sw_variants[i] == self.sw_one and \
                            subframe_sw_variants[i] == self.sw_two:
                    #if frame_sw_variants[i] == self.sw_one:
                        found_sw = True
                        self.bytes_counter -= (self.frame_len + 4)
                        self.mix_type = i
                        break
                        #------------------------------------------------------
                        #print("found mix type")
                        #print("mix type is # %s" % self.mix_type)
                    else:
                        self.bytes_counter -= self.frame_len
                else:
                    i += 1

    def mix_syncword(self, four_bytes):
        """ Convert words by four types of mix schemes """
        bin_str = ""
        mixed_words = []  # 8 items list
        byte_size = 8
        for byte in four_bytes:
            #-----convert byte to binary representation---------
            #-----exclude "0b" at start and fill with ----------
            #-----zeros at the beginning to make 8 symbols------
            bin_str += ((bin(ord(byte)))[2:]).zfill(byte_size)

        #------type one |3|5|8|7|1|------------
        # 0 index/first subword
        mixed_words.append(bin_str[23:24] + bin_str[8:16] + bin_str[:3])
        # 1 index/second subword
        mixed_words.append(bin_str[27:32] + bin_str[16:23])

        #------type two |5|3|1|7|8|------------
        # 2 index/first subword
        mixed_words.append(bin_str[9:16] + bin_str[:5])
        # 3 index/second subword
        mixed_words.append(bin_str[29:32] + bin_str[16:24] + bin_str[8:9])

        #------type three |8|4|4|8|------------
        # 4 index/first subword
        mixed_words.append(bin_str[12:16] + bin_str[:8])
        # 5 index/second subword
        mixed_words.append(bin_str[16:24] + bin_str[8:12])

        #------type four |6|2|2|6|8|------------
        # 6 index/first subword
        mixed_words.append(bin_str[10:16] + bin_str[:6])
        # 7 index/second subword
        mixed_words.append(bin_str[30:32] + bin_str[16:24] + bin_str[8:10])

        return mixed_words

    def mix_words(self, bytes_to_mix):
        """ Create 16 bit words from 12 bit words
                         to be recorded in target file """
        middle = self.mix_syncword(bytes_to_mix)
        tmp_str_1 = "0000" + middle[self.mix_type]
        tmp_str_2 = "0000" + middle[self.mix_type + 1]
        mixed_words = [tmp_str_1, tmp_str_2]
        #mixed_words = [tmp_str_1[8:16], tmp_str_1[0:8],
                       #tmp_str_2[8:16], tmp_str_2[0:8]]
        return mixed_words

    def extract_time(self, converted):
        try:
            hours_bin = converted[156][:9]
            minutes_bin = converted[156][9:-1]
            seconds_bin = converted[157][:10]
            hour = int(hours_bin, 2)
            if hour > 23:
                hour = 23
            minute = int(minutes_bin, 2)
            sec = int(seconds_bin, 2)
            date = datetime.datetime(year=2015, month=1, day=1,
                                     hour=hour, minute=minute, second=sec)
            self.start_date.append(date)
        except IndexError:
            date = datetime.datetime(year=2015, month=1, day=1,
                                     hour=0, minute=0, second=0)
            self.start_date.append(date)
