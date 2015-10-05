#-*-coding: utf-8-*-

import datetime
import win32api

SAVE_OPTION = "__save__"


class HeaderType32Bytes(object):

    def __init__(self, path, qar_type):
        self.header_len = 32  # Bytes
        self.frame_len = None  # 768  # Bytes
        self.cluster_size = None  #8192
        self.frame_duration = None  #2  # sec
        self.qar_type = qar_type
        self.path_save = None
        self.compact_flash_size = None  #500400*512  # 512MB
        self.start_date = []  # flights start date
        self.headers = []
        self.header_pattern = [4, 3]
        self.syncword_one = ["4", "3"]
        self.bytes_counter = 0
        self.flights_start = []
        self.flight_intervals = []
        self.durations = []  # flights durations
        self.time = []
        self.end_date = []  # flights end date
        self.current_flight = None

    def copy_cf_data(self):
        """ Copy data from Compact Flash into temporary
        file on computer drive C or to place specified by user.
        This ensure more convenient and quick data access """
        if self.path_save:  # if user has chosen path to save
            copy_name = u"%s_cf.tmp" % self.path_save
        else:
            copy_name = str(win32api.GetTempPath()) + "cf.tmp"
        new_file = open(copy_name, "wb")
        counter = 0
        read_chunk = 512  # amount of bytes to read at a time
        while counter < self.compact_flash_size:
            new_file.write(self.dat.read(read_chunk))
            counter += read_chunk
        self.dat.close()
        new_file.close()
        return copy_name

    def find_start(self):
        while self.bytes_counter < self.source_len - self.cluster_size:
            flights_start = self.find_syncword()
            if flights_start:
                break

    def find_syncword(self):
        byte_amount = len(self.syncword_one)
        while self.bytes_counter < self.source_len - self.cluster_size - 16:
            syncword = []
            for each in self.syncword_one:
                byte_one = self.source.read(1)
                try:
                    syncword.append(str(ord(byte_one)))
                except TypeError:  # end of file
                    break
            if syncword == self.syncword_one:
                # add start and header of first flight
                current_pos = self.source.tell()
                self.flights_start.append(self.bytes_counter)
                self.source.seek(-byte_amount, 1)
                self.headers.append(self.source.read(self.header_len))
                flight = self.headers[0][3]
                flight_num = int('0' + (hex(ord(flight)))[2:])
                self.current_flight = flight_num
                self.source.seek(-self.header_len, 1)
                return True
            else:
                # in case of 2 byte syncword we need to go back one byte
                # correspondingly in case of 2 byte sw - we increase bytes_counter
                self.source.seek(-(byte_amount - 1), 1)
                self.bytes_counter += (byte_amount - 1)

    def find_flights(self):
        """ Using header pattern and notion that headers are written
        at the start of each 8KB cluster find all flights` starts.
        Distinguish flights by their flight numbers -> 2-3 bytes"""
        for each_index in range(self.flights_start[0]+self.cluster_size, self.source_len, self.cluster_size):
            self.source.seek(each_index, 0)
            self.bytes_counter += self.cluster_size
            next_byte = self.source.read(1)
            try:
                if (ord(next_byte) == self.header_pattern[0] and
                        ord(self.source.read(1)) == self.header_pattern[1]):
                    # check flight number
                    self.source.seek(1, 1)
                    flight = self.source.read(1)
                    flight_num = ord(flight)
                    if flight_num == self.current_flight:
                        pass
                    else:
                        self.flights_start.append(self.bytes_counter)
                        self.source.seek(each_index, 0)  # amount of syncword in bytes
                        self.headers.append(self.source.read(self.header_len))
                        self.current_flight = flight_num
            except TypeError:  # no more bytes with data -> empty bytes at the end
                break

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start):
            try:
                self.flight_intervals.append([self.flights_start[i],
                                              self.flights_start[i+1]])
            except IndexError:
                self.flight_intervals.append([self.flights_start[i],
                                              self.get_last_flight_end(self.flights_start[i])])
            i += 1

    def get_last_flight_end(self, start):
        """ As there is no way to get another header after last flight,
        simply process bytes starting from last flight start index
        and search for end flight pattern, which is chunk of zeros """
        self.source.seek(start, 0)
        bytes_counter = start
        end_pattern = [0]*48
        while True:
            next_byte = self.source.read(1)
            if next_byte == "":  #EOF
                return bytes_counter
            bytes_counter += 1
            if ord(next_byte) == 0:
                next_48_bytes = self.source.read(48)
                prev_bytes_list = [ord(each) for each in next_48_bytes]
                if prev_bytes_list == end_pattern:
                    return bytes_counter
                else:
                    bytes_counter += 48

    def get_flights_start(self):
        for header in self.headers:
            year = '20' + (hex(ord(header[15])))[2:]

            month = '0' + (hex(ord(header[14])))[2:] if \
                           len((hex(ord(header[14])))[2:]) == 1 else \
                           (hex(ord(header[14])))[2:]

            day = '0' + (hex(ord(header[13])))[2:] if \
                         len((hex(ord(header[13])))[2:]) == 1 else \
                         (hex(ord(header[13])))[2:]

            hour = '0' + (hex(ord(header[11])))[2:] if \
                          len((hex(ord(header[11])))[2:]) == 1 else \
                          (hex(ord(header[11])))[2:]

            minute = '0' + (hex(ord(header[10])))[2:] if \
                            len((hex(ord(header[10])))[2:]) == 1 else \
                            (hex(ord(header[10])))[2:]

            second = '0' + (hex(ord(header[9])))[2:] if \
                            len((hex(ord(header[9])))[2:]) == 1 else \
                            (hex(ord(header[9])))[2:]

            start_date = datetime.datetime(int(year), int(month), int(day),
                                           int(hour), int(minute), int(second))
            self.start_date.append(start_date)
            #print self.start_date

    def get_flights_duration(self):
        duration = []
        duration_cluster = []
        for header in self.headers:
            clusters_num = (header[4], header[5], header[6], header[7])
            clusters = '0x'
            for each in clusters_num:
                if len((hex(ord(each)))[2:]) == 1:
                    clusters += '0' + (hex(ord(each)))[2:]
                else:
                    clusters += (hex(ord(each)))[2:]
            current_clusters = int(clusters, 16)
            duration.append(current_clusters)
        i = 0
        while i < len(duration) - 1:
            duration_cluster.append(duration[i+1] - duration[i])  # amount of clusters
            i += 1
        for each in duration_cluster:
            duration_time = ((each * self.cluster_size) / self.frame_len) * self.frame_duration  # in sec
            self.durations.append(duration_time)
        #------ Calculate duration for last flight ---------
        last_dur = self.flight_intervals[-1][1] - self.flight_intervals[-1][0]  # Bytes
        dur = (last_dur / self.frame_len) * self.frame_duration
        self.durations.append(dur)

    def get_flights_end(self):
        i = 0
        while i < len(self.start_date):
            flight_end = self.start_date[i] + datetime.timedelta(seconds=int(self.durations[i]))
            self.end_date.append(flight_end)
            i += 1
