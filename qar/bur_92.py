import os
import datetime
import struct
import win32api
from source_data import QAR_TYPES


class Bur(object):

    """
        if An148 with no header then it has technical info inside
        1.create second file - cleaned from technical info and save
        2.work with cleaned file
        3.mark cleaned file with F5 5F at the beginning
        4. on file opening check if F% 5F is at the beginning - no need to cleaned
    """

    def __init__(self, path, chosen_acft_type, progress_bar):
        self.path = path
        self.dat = open(path, "rb")
        self.file_len = os.stat(path).st_size
        self.chosen_acft_type = chosen_acft_type
        self.qar_type = QAR_TYPES[self.chosen_acft_type][1]
        self.start = False
        self.syncword_one = [0, 0]
        self.flights_start = []
        self.flights_end = []
        self.flight_intervals = []
        self.durations = []
        self.start_date = []
        self.end_date = []
        self.flights_ids = []
        if self.qar_type == "bur92_header":
            # in order to avoid header and starting "noises" for record with header
            self.bytes_counter = 12800
            self.dat.seek(12800, 0)
        else:  # record with no header - records are continuously overwritten each other
            self.bytes_counter = 0
        self.frame_size = 512  # byte
        self.frame_duration = 1  # sec
        self.end_check = [255] * 4
        self.end_pattern = [255] * self.frame_size
        self.progress_bar = progress_bar

        if self.qar_type == "bur92_no_header":
            check = self.check_if_clean()
            if not check:
                self.clean_file()

        self.find_start()
        self.get_flights()
        self.progress_bar.SetValue(25)

        self.get_flight_intervals()
        self.progress_bar.SetValue(45)

        self.get_durations()
        self.progress_bar.SetValue(65)

        self.get_date_time()
        self.get_flight_ids()
        self.progress_bar.SetValue(85)

        self.get_flight_ends()
        self.progress_bar.SetValue(95)

    def check_if_clean(self):
        first_two_byte = self.dat.read(2)
        word_one = ord(first_two_byte[0])
        word_two = ord(first_two_byte[1])
        print word_one, word_two
        if word_one == 245 and word_two == 95:
            self.bytes_counter = 2
            return True
        else:
            self.dat.seek(0)
            return False

    def clean_file(self):
        """ in an148 bur92 with no header there is technical info which repeats through the whole file
            Clean file from technical info
            technical info appears each 2048 bytes
            the length of technical info is 64 bytes
            thus the length of data + technical info is 2112 bytes
            it has to be removed from file before saving flights

            1. copy flight data skipping technical info
            """
        info_size = 64  # bytes
        interval = 2112 # bytes
        segment_length = 2048
        # go to the propper index in the file
        # copy infor from the start index till first technical info (2048 byte)
        # copy all info skipping each 64 bytes with 2112 bytes interval
        new_file_name = self.path[:-4] + "_clean.dat"
        new_file = open(new_file_name, "wb")
        byte_one = "11110101"
        byte_two = "01011111"
        for each in [byte_one, byte_two]:
            str_to_int = int(each, 2)
            data_to_write = struct.pack("i", str_to_int)
            new_file.write(data_to_write[:1])
        new_file.write(self.dat.read(segment_length))
        bytes_counter = segment_length
        while bytes_counter < self.file_len:
            self.dat.seek(info_size, 1)
            new_file.write(self.dat.read(segment_length))
            bytes_counter += interval
        # close the original file and reopen newly created and work with it
        self.dat.close()
        new_file.close()
        # by this reassignment - we also provide new path to qar_reader.py to get data from it when saving flights
        self.path = new_file_name
        self.dat = open(new_file_name, "rb")
        self.file_len = os.stat(new_file_name).st_size



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
        """ An148 can be with or without header.

            -> If it has header go to index 12800 and from there look for syncword - 00 00

            -> If there is no header - it means that record can start from teh beginning of the file and
            starting from 2048 byte each 2112 byte there are 64 byte of technical information.
            This info is not necessary and need to be deleted

            """
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
        # if for the last flight end is not found - add the index of file end
        # in other words that last flight will end by flight ending
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
        """
                   An 148

        time and date are recorded at the beginning of each frame
        (each 512 starting with 00 00 - 1st and 2d bytes):
        - seconds at 3-4 B
        - minutes at 5-6 B
        - hours at 7-8 B
        - year is recorded only at frame where seconds == 3
        - month is recorded only at frame where seconds == 4
        - day is recorded only at frame where seconds == 5
        In order to get stable time -> find 'middle flight time'
        and then get start and end flight time
        knowing amount of frames in flight

                    An 140

        - get first frame
        - after frame start 00 00 take time and path as start time
        - seconds at 3 and 4 bytes
        - minutes at 5 and 6 bytes
        - hours at 7 and 8 bytes
        - for each part of time - switch bytes, make inversion, get decimal value
        """

        if QAR_TYPES[self.chosen_acft_type][0] == "an140":
            for each in self.flight_intervals:
                start = each[0]
                end = each[1]
                self.dat.seek(start, 0)
                first_frame = self.dat.read(self.frame_size)
                sec = self.convert_data(first_frame[2:4])
                minute = self.convert_data(first_frame[4:6])
                hour = self.convert_data(first_frame[6:8])
                sec_decimal = int(sec, 2)
                min_decimal = int(minute, 2)
                hour_decimal = int(hour, 2)
                year = 2014
                month = 1
                day = 1
                start_date_time = datetime.datetime(year=year, month=month, day=day,
                                                    hour=hour_decimal, minute=min_decimal, second=sec_decimal)
                self.start_date.append(start_date_time)

        else:

            try:
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
                        sec = self.convert_data(one_frame[2:4])
                        sec_ord = self.convert_in_ord(sec)
                        #print sec_ord
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
            except TypeError:  # something is wrong with data type
                for each in self.flight_intervals:
                    start_date_time = datetime.datetime(year=2000, month=1, day=1,
                                                        hour=0, minute=0, second=0)
                    self.start_date.append(start_date_time)

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
                minutes = int(self.convert_in_ord(value[0]))
                hours = int(self.convert_in_ord(value[1]))
                year = int("20" + str(self.convert_in_ord(value[2])))
            elif key == 4:
                month = int(self.convert_in_ord(value[2]))
            elif key == 5:
                day = (self.convert_in_ord(value[2]))
        if minutes < 0:
            minutes = 0
        elif minutes > 59:
            minutes = 59
        print year, month, day, hours, minutes, sec
        middle_date_time = datetime.datetime(year=year, month=month, day=day,
                                             hour=hours, minute=minutes, second=sec)
        return middle_date_time

    def get_flight_ends(self):
        i = 0
        for each in self.start_date:
            end_date = each + datetime.timedelta(seconds=self.durations[i])
            self.end_date.append(end_date)
            i += 1

    def get_flight_ids(self):
        for each in self.flight_intervals:
            self.flights_ids.append(0)

class BUR92AN140(object):

    def __init__(self, tmp_file_name, target_file_name, progress_bar,
                 path_to_save, flag):
        self.source_file = open(tmp_file_name, "rb")
        self.target_file = open(r"%s" % path_to_save + r"\\" +
                                r"%s" % target_file_name, "w")
        self.progress_bar = progress_bar
        self.flag = flag
        self.bytes_counter = 0
        self.source_size = os.stat(tmp_file_name).st_size
        self.channels_per_frame = (QAR_TYPES[flag][2])/2

        self.record_data_as_decimal_in_text()

    def record_data_as_decimal_in_text(self):
        channels_in_frame = 0
        while self.bytes_counter < self.source_size-2:
            bytes_in_channel = self.get_channel_bytes()
            switched_bytes = self.switch_bytes(bytes_in_channel)
            inverse_bytes = self.inverse_bytes(switched_bytes)
            channels_in_frame += 1
            if channels_in_frame < self.channels_per_frame:
                self.target_file.write("%s;" % inverse_bytes)
            elif channels_in_frame == self.channels_per_frame:
                self.target_file.write("%s\n" % inverse_bytes)
                channels_in_frame = 0

    def get_channel_bytes(self):
        channel = self.source_file.read(2)
        self.bytes_counter += 2
        return [ord(each) for each in channel]

    def switch_bytes(self, bytes_in_channel):
        return [bytes_in_channel[1], bytes_in_channel[0]]

    def inverse_bytes(self, bytes_ord):
        channel_bin_str = ""
        for each in bytes_ord:
            channel_bin_str += ((str(bin(each)))[2:]).rjust(8, "0")
        channel_inverse_bin_str = ''.join(["1" if symbol == "0" else "0" for symbol in channel_bin_str])
        channel = int(channel_inverse_bin_str, 2)
        return channel


class Bur4T(object):

    """  BUR-4T
         data is written in 160 byte frames by 10 bits word
         syncwords are parts of original ARINC syncwords

         frame starts with fourth (ARINC reverse) syncword and only with last 8 bits

         ARINC reverse fourth syncword - 000111011011
         bur-4t first syncword - 11011011

         1. find all valid frames (by first syncwords)
         2. convert data from 10 bit words to 16 bit words (by adding 000000 at the beginning)
            starting from the first syncword
         3. record to file
    """

    def __init__(self, path, chosen_acft_type, progress_bar, path_to_save):
        self.path = path
        self.data = open(self.path, "rb").read()
        self.data_len = os.stat(path).st_size
        self.start = 0
        self.bytes_counter = 0
        self.current_position = 0
        self.chosen_acft_type = chosen_acft_type
        self.progress_bar = progress_bar
        self.sw_one = "11011011"  # last 8 bits of ARINC reverse fourth syncword
        self.frame_len = QAR_TYPES[self.chosen_acft_type][2]  # in bytes
        self.frame_len_bits = 1280
        self.data_end = False
        self.first_frame = None
        self.path_to_save = path_to_save
        self.word_size = 10
        self.board_number = None
        self.flight_number = None
        self.data_len_in_bits = self.data_len * 8

        self.progress_bar.Show()
        self.progress_bar.SetValue(15)

        self.str_data = self.convert_data_to_str()
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)
        self.target_file.close()

    def convert_data_to_str(self):
        """ convert from bytes to binary string representation """
        result = []
        for each in self.data:
            result.append((str(bin(ord(each)))[2:]).rjust(8, "0"))
        return ''.join(result)

    def record_data(self):
        while self.current_position < self.data_len_in_bits and not self.data_end:
            self.find_start()
            while self.start:
                self.current_position = self.start
                frame = self.check_next_frame()
                if not frame:
                    break
                else:
                    self.write_frame(frame)

    def find_start(self):
        # todo: redo this method
        while self.current_position < self.data_len_in_bits and not self.data_end:
            syncword_index = self.str_data.find(self.sw_one, self.current_position)
            next_syncword = self.str_data.find(self.sw_one, syncword_index + self.frame_len_bits)
            if next_syncword - syncword_index == self.frame_len_bits:
                self.start = syncword_index
                next_syncword_index = self.str_data.find(self.sw_one, next_syncword + self.frame_len_bits)
                if next_syncword_index - next_syncword == self.frame_len_bits:
                    next_next_syncword = self.str_data.find(self.sw_one, next_syncword_index + self.frame_len_bits)
                    if next_next_syncword - next_syncword_index == self.frame_len_bits:
                        # get first 2 frames to get from them board number and flight number
                        self.first_frame = self.str_data[self.start:self.start + self.frame_len_bits * 2]
                        # as soon as we got first two frames of a flight - get board and flight number
                        self.get_boardN_flightN_in_path_to_save()
                        # and modify name of a file to save
                        self.form_file_name()
                        break
            self.current_position += 1

    def write_frame(self, frame):
        # todo: call this method from converter class
        i = 0
        while i < len(frame):
            word = frame[i:i+self.word_size]
            # insert zeroes
            bytes_to_write = ["000000" + word[:2], word[2:]]
            for each in bytes_to_write:
                str_to_int = int(each, 2)
                data_to_write = struct.pack("i", str_to_int)
                self.target_file.write(data_to_write[:1])
            i += self.word_size

    def check_next_frame(self):
        next_syncword = self.str_data.find(self.sw_one, self.current_position + self.frame_len_bits)
        if next_syncword == -1:  # end of file - no more syncwords
            self.data_end = True
            return
        if next_syncword - self.start == self.frame_len_bits:
            frame = self.str_data[self.current_position:next_syncword]
            self.start = next_syncword
            return frame
        else:
            return False

    def get_boardN_flightN_in_path_to_save(self):
        """ convert first 2 frames to 16 bit words to get data from it
            - board number is in 160, 161 bytes starting from the frame beginning
            - flight number is in 224, 225 bytes starting from the frame beginning
            each of these number should be processed as following:
            1. get two bytes - 00000011 10110011
            2. make shift by two lower bits and take 8 bits - 11101100
            3. make full inversion 00010011 or get its ord value and make 255 - ord(11101100)
        """
        board_start_bit = 160 * 8  # bits to start from
        flight_start_bit = 224 * 8  # bits to starts from
        converted_frame = []
        i = 0
        while i < len(self.first_frame):
            word = self.first_frame[i:i+self.word_size]
            # insert zeroes
            converted_word = "000000" + word
            converted_frame.append(converted_word)
            i += self.word_size
        str_converted_frame = ''.join(converted_frame)
        board_channel = str_converted_frame[board_start_bit:board_start_bit + 16]  # two bytes to read
        flight_channel = str_converted_frame[flight_start_bit:flight_start_bit + 16]   # two bytes to read
        board = board_channel[6:-2]  # take only necessary bits
        flight = flight_channel[6:-2]   # take only necessary bits
        self.board_number = 255 - int(board, 2)
        self.flight_number = 255 - int(flight, 2)

    def form_file_name(self):
        date_time_now = datetime.datetime.now().strftime("%Y.%m.%d_%H_%M_%S")
        self.name = "MI_24_{}_{}_{}.inf".format(self.board_number, self.flight_number, date_time_now)
        self.target_file = open(r"%s" % self.path_to_save + r"\\" + r"%s" % self.name, "wb")


class BUR1405(object):
    """ An26 Bur 1-4-05 display flights
        - Starting from index 512B - 16B of technical info goes after each 512B
          (between end of first technical info and beginning os second - 512 bytes)
        - Delete all technical info
        - Each flight ends with 7 FF
        - Date set to 01.01.2015
        - Time take as following:
          starting from the first information byte
            17 byte - sconds
            81 byte - minutes
            209 byte - hours

        If file with flights is opened first - undergo all necessary conversions and removing headers.

        If it was opened before - therefore already converted - no need to convert it again - just extract flights

    """

    def __init__(self, path, chosen_acft_type):
        self.path = path
        self.chosen_acft_type = chosen_acft_type
        self.copy_file_path = os.path.splitext(self.path)[0] + ".inf"
        self.search_frame_len = QAR_TYPES[self.chosen_acft_type][2]
        self.data_frame_len = 160  # TODO: redo this
        self.qar_type = QAR_TYPES[self.chosen_acft_type][1]
        self.header_size = 16
        self.end_pattern = 7  # FF
        self.source_file = open(self.path, 'rb')
        self.source_len = os.stat(path).st_size
        self.start = False
        self.data_start = []
        self.bytes_counter = 0
        self.first_syncword = "11011011"
        self.second_syncword = "00100101"
        self.third_syncword = "11011010"
        self.fourth_syncword = "00100100"
        self.data_frame_len_in_bits = self.data_frame_len * 8
        self.flight_first_frame = []
        self.flights_start = []
        self.flights_end = []
        self.data_end = False
        self.flight_intervals = []
        self.durations = []
        self.start_date = []
        self.end_date = []
        self.key_word = ['10101010', '11111111', '10101010', '11111111']  # in hex AA FF AA FF
        self.checked = False

        self.check_file()

        if self.checked:
            self.find_flights()
            self.get_flight_intervals()
            self.get_durations()
            self.get_start_date()
            self.get_end_date()
        else:
            self.find_start()
            self.remove_all_headers()
            self.find_flights()
            self.get_flight_intervals()
            self.get_durations()
            self.get_start_date()
            self.get_end_date()

    def check_file(self):
        """ If first bytes in file are checked - no need to do conversions """
        if [str(bin(ord(each)))[2:] for each in self.source_file.read(4)] == self.key_word:
            self.checked = True
            self.source_file.close()
            self.clear_copy = open(self.path, 'rb')
            self.clear_copy_size = os.stat(self.copy_file_path).st_size
        else:
            self.source_file.seek(0, 0)
            self.clear_copy = open(self.copy_file_path, "wb")

    def find_start(self):

        """ Flights start at index 512
            1. Check for header - store first byte
            2. Pass 512 bytes
            3. Repeat 1 and 2 steps three times
            4. If first bytes increments by 1 (its a counter) - first header index is a start
        """

        while not self.start:
            self.get_header()
            if len(self.data_start) == 3:
                # check its incrementing and
                if self.data_start[2][1] - self.data_start[1][1] == 1 and self.data_start[1][1] - self.data_start[0][1] == 1:
                    self.start = self.data_start[0][0]
                    self.source_file.seek(self.start + self.header_size, 0)
                else:
                    # if it is not incrementing - start right after first header
                    self.source_file.seek(self.data_start[0][0] + self.header_size, 0)
                    self.data_start = []  # clear it to get new data

    def get_header(self):
        self.source_file.seek(self.search_frame_len, 1)
        self.bytes_counter = self.source_file.tell()
        header = self.source_file.read(self.header_size)
        self.data_start.append([self.bytes_counter, int(ord(header[0]))])
        return

    def remove_all_headers(self):
        """ Not to change original file - store data without headers in separate tmp file
            In order not to do all these steps for headers removal and other checks - create a copy of orginal file
            cleared from header.
            Mark this file as already cleaned - so this property could be checked next time
        """
        for element in self.key_word:
            self.clear_copy.write((struct.pack("i", int(element, 2)))[:1])
        while self.bytes_counter < self.source_len - self.search_frame_len:
            self.clear_copy.write(self.source_file.read(self.search_frame_len))
            self.source_file.seek(self.header_size, 1)
            self.bytes_counter = self.source_file.tell()
        self.clear_copy.close()  # close - because it was opened for writing before - and now we need to read from it
        self.clear_copy = open(self.copy_file_path, 'rb')
        self.clear_copy_size = os.stat(self.copy_file_path).st_size
        self.bytes_counter = 0

    def find_flights(self):
        while self.bytes_counter < self.clear_copy_size - self.data_frame_len:
            self.find_flight_start()
            self.find_flight_end()
            self.extract_all_ff_at_flight_end()

    def find_flight_start(self):
        self.bits_counter = 0
        while self.bytes_counter < self.clear_copy_size - self.data_frame_len:
            frames = self.clear_copy.read(self.data_frame_len * 3)
            frames_in_str = [(str(bin(ord(data)))[2:]).rjust(8, "0") for data in frames]
            frames_in_bin = ''.join(frames_in_str)
            #---------------------------------------
            first_syncword_index = frames_in_bin.find(self.first_syncword, self.bits_counter)
            second_syncword_index = frames_in_bin.find(self.second_syncword, first_syncword_index + 320)
            third_syncword_index = frames_in_bin.find(self.third_syncword, second_syncword_index + 320)
            fourth_syncword_index = frames_in_bin.find(self.fourth_syncword, third_syncword_index + 320)

            if (fourth_syncword_index - third_syncword_index == 320 and
                third_syncword_index - second_syncword_index == 320 and
                second_syncword_index - first_syncword_index == 320):
                self.flight_first_frame.append(frames_in_bin[first_syncword_index:fourth_syncword_index + self.data_frame_len_in_bits])
                self.flights_start.append(self.bytes_counter)
                return
            else:
                self.bits_counter = first_syncword_index + len(self.first_syncword)
                self.bytes_counter = self.clear_copy.tell()

    def find_flight_end(self):
        while self.bytes_counter < self.clear_copy_size - self.data_frame_len:
            few_frames = self.clear_copy.read(self.data_frame_len)
            frames_in_ord = [str(ord(data)) for data in few_frames]
            frames = ''.join(frames_in_ord)
            end_pattern = '255'*7
            if end_pattern in frames:
                self.bytes_counter = self.clear_copy.tell()
                self.flights_end.append(self.bytes_counter)
                return
            else:
                self.bytes_counter = self.clear_copy.tell()

    def extract_all_ff_at_flight_end(self):
        while True:
            check_byte = self.clear_copy.read(1)
            try:
                val = ord(check_byte)
                if val == 255:
                    pass
                else:
                    self.bytes_counter = self.clear_copy.tell()
                    return
            except TypeError:
                self.bytes_counter = self.clear_copy_size
                return

    def get_flight_intervals(self):
        """ if the length of start and ends is different - starts are greater on one index
            add source size as the last end
        """
        if len(self.flights_start) - len(self.flights_end) == 1:
            self.flights_end.append(self.clear_copy_size)
        self.flight_intervals = zip(self.flights_start, self.flights_end)

    def get_durations(self):
        """ 1. End - start = bytes
            2. Bytes * 8 = bits
            3. Bits / 10 = amount of 10bit channels
            4. amount of 10bit channels * 6 = amount of bits (000000) to add
            5. bits + amount of bits to add = tot bits after adding zeros
            6. tot bits / 8 = amount of bytes
            7. amount of bytes / 256 = seconds
        """
        each_flight_bits = map(lambda start, end: (end - start)*8, self.flights_start, self.flights_end)
        each_flight_channels = map(lambda start, end: ((end - start)*8)/10, self.flights_start, self.flights_end)
        each_flight_additional_zeros = map(lambda bits: bits * 6, each_flight_channels)
        self.durations = map(lambda bits, zeros: ((bits + zeros)/8)/256, each_flight_bits, each_flight_additional_zeros)

    def get_start_date(self):
        """ Get time from first two frames of each flight
            - make data 16 bit words out of 10 bit words:
                take 10 bit and + '000000' in front of it
            - take corresponding byte for each time value
            - take first 6 bits
            - inverse them
            - get decimal representation for time
        """
        sec_index = 8 * 17
        min_index = 8 * 81
        hour_index = 8 * 209
        for each in self.flight_first_frame:
            i = 0
            converted_first_frame = ""
            while i < len(each):
                converted_first_frame += "000000" + each[i:i+10]
                i += 10
            original_sec_value = (converted_first_frame[sec_index:sec_index + 6])
            original_min_value = (converted_first_frame[min_index:min_index + 6])
            original_hour_value = (converted_first_frame[hour_index:hour_index + 6])
            inverse_sec_value = ''.join(['1' if number == "0" else "0" for number in original_sec_value])
            inverse_min_value = ''.join(['1' if number == "0" else "0" for number in original_min_value])
            inverse_hour_value = ''.join(['1' if number == "0" else "0" for number in original_hour_value])
            sec_value = int(inverse_sec_value, 2)
            min_value = int(inverse_min_value, 2)
            hour_value = int(inverse_hour_value, 2)
            start_date_time = datetime.datetime(year=2015, month=1, day=1,
                                                hour=hour_value, minute=min_value, second=sec_value)
            self.start_date.append(start_date_time)

    def get_end_date(self):
        self.end_date = map(lambda start, duration: start + datetime.timedelta(seconds=duration),
                            self.start_date, self.durations)


class BUR1405Data(object):

    def __init__(self, tmp_file_name, target_file_name, progress_bar, path_to_save, chosen_acft_type):
        self.source = open(tmp_file_name, "rb")
        self.source_len = os.stat(tmp_file_name).st_size
        self.param_file = open(r"%s" % path_to_save + r"\\" +
                               r"%s" % target_file_name, "wb")
        self.progress_bar = progress_bar
        self.chosen_acft_type = chosen_acft_type
        self.first_syncword  = "11011011"
        self.second_syncword = "00100101"
        self.third_syncword  = "11011010"
        self.fourth_syncword = "00100100"
        self.bits_counter = 0

        self.progress_bar.Show()

        self.record_flight()
        self.progress_bar.SetValue(100)

    def record_flight(self):
        data = self.find_flight_start()
        self.progress_bar.SetValue(35)
        i = 0
        while True:
            try:
                ten_bit_word = data[i:i+10]
                sixteen_bit_word = "000000" + ten_bit_word
                data_to_write = [int(sixteen_bit_word[:8], 2), int(sixteen_bit_word[8:], 2)]
                for each in data_to_write:
                    self.param_file.write(struct.pack("i", each)[:1])
                i += 10
            except:
                break
        self.progress_bar.SetValue(85)

    def find_flight_start(self):
        self.progress_bar.SetValue(5)
        frames = self.source.read()
        frames_in_str = [(str(bin(ord(data)))[2:]).rjust(8, "0") for data in frames]
        frames_in_bin = ''.join(frames_in_str)
        # while True:
        #     first_syncword_index = frames_in_bin.find(self.first_syncword, self.bits_counter)
        #     second_syncword = frames_in_bin.find(self.second_syncword, first_syncword_index + 320)
        #     if second_syncword - first_syncword_index == 320:
        #         self.progress_bar.SetValue(15)
        #         return frames_in_bin[first_syncword_index:]
        #     else:
        #         self.bits_counter = first_syncword_index + 10
        while True:
            first_syncword_index = frames_in_bin.find(self.first_syncword, self.bits_counter)
            second_syncword_index = frames_in_bin.find(self.second_syncword, first_syncword_index + 319)
            third_syncword_index = frames_in_bin.find(self.third_syncword, second_syncword_index + 319)
            fourth_syncword_index = frames_in_bin.find(self.fourth_syncword, third_syncword_index + 319)
            if (fourth_syncword_index - third_syncword_index == 320 and
                third_syncword_index - second_syncword_index == 320 and
                second_syncword_index - first_syncword_index == 320):
                sequence_to_write = frames_in_bin[first_syncword_index:]
                self.progress_bar.SetValue(15)
                return sequence_to_write
            else:
                self.bits_counter = first_syncword_index + len(self.first_syncword)
