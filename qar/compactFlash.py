#-*-coding: utf-8-*-
import os
import datetime
import time
import win32api


class CompactFlash(object):

    """  Compact Flash Header description (complete description is absent)

    Header length: 32 B

    0 - 1: header pattern (in present case -> 0403 (hex))
    2 - 3: flight number (as it is) -> if there is 27 - it means 27th flight
    4 - 5: may be part of cluster #
    6 - 7: cluster # (hex)
    9: seconds (as it is)
    10: minutes (as it is)
    11: hours   (as it is)
    12: day     (as it is)
    13: month   (as it is)
    14: year    (last two digits as it is) """

    def __init__(self, path):
        self.header_len = 32  # Bytes
        self.frame_len = 768  # Bytes
        self.cluster_size = 8192
        self.frame_duration = 2  # sec
        self.qar_type = "a320_cf"
        self.path = path
        transformed_path = r"\\.\%s" % self.path[:2]
        self.dat = file(transformed_path, "rb")
        self.compact_flash_size = 500400*512  # 512MB
        self.start_date = []  # flights start date
        self.headers = []
        self.header_pattern = []
        self.bytes_counter = 0
        self.flights_start = []
        self.flight_intervals = []
        #self.durations_int = []
        self.durations = []  # flights durations
        self.time = []
        self.end_date = []  # flights end date
        #------ Copy data from compact flash into tmp file on desktop ---------
        copy_file = self.copy_cf_data()
        self.source = open(copy_file, "rb")
        self.source_len = os.stat(copy_file).st_size
        #------ Define pattern with which starts every header -----------------
        self.get_header_pattern()
        #------ Search for flights start -------------------------------------
        self.find_flights()
        self.get_flight_intervals()
        self.get_flights_start()
        self.get_flights_duration()
        self.get_flights_end()
        # re-assignment due to use os self.path for future processing
        self.path = copy_file

    def copy_cf_data(self):
        """ Copy data from Compact Flash into temporary file on computer drive C.
        This ensure more convenient and quick data access """
        copy_name = str(win32api.GetTempPath()) + "cf.tmp"
        #copy_name = r"C:\\cf.tmp"  # when should I delete this file?
        new_file = open(copy_name, "wb")
        counter = 0
        read_chunk = 512  # amount of bytes to read at a time
        while counter < self.compact_flash_size:
            new_file.write(self.dat.read(read_chunk))
            counter += read_chunk
        self.dat.close()
        new_file.close()
        return copy_name

    def get_header_pattern(self):
        """ Determine how each header start (by the first one)
        and then use this pattern for headers chech within file """
        while not self.header_pattern:
            next_byte = self.source.read(1)
            self.bytes_counter += 1
            if ord(next_byte) != 0:
                self.source.seek(-1, 1)
                self.bytes_counter -= 1
                self.headers.append(self.source.read(self.header_len))
                self.header_pattern.append(ord(self.headers[0][0]))
                self.header_pattern.append(ord(self.headers[0][1]))
                self.flights_start.append(self.bytes_counter)  # first flight start
                self.source.seek(-self.header_len, 1)

    def find_flights(self):
        """ Using header pattern and notion that headers are written
        at the start of each 8KB cluster find all flights` starts.
        Before start flight header a chunk of zeros
        (of different size) is present """
        while self.bytes_counter < self.source_len - self.cluster_size - 16:
            self.source.seek(self.cluster_size, 1)
            self.bytes_counter += self.cluster_size
            next_byte = self.source.read(1)
            try:
                if (ord(next_byte) == self.header_pattern[0] and
                    ord(self.source.read(1)) == self.header_pattern[1]):
                    # check previous 48 bytes
                    self.source.seek(-50, 1)
                    prev_48_bytes = self.source.read(48)
                    prev_bytes_list = [ord(each) for each in prev_48_bytes]
                    end_pattern = [0]*48
                    if prev_bytes_list == end_pattern:  # if all zeros
                        self.flights_start.append(self.bytes_counter)
                        self.headers.append(self.source.read(self.header_len))
                        self.source.seek(-self.header_len, 1)
            except TypeError:  # no more bytes with data -> empty bytes at the end
                break

    def get_flight_intervals(self):
        i = 0
        while i < len(self.flights_start):
            try:
                self.flight_intervals.append([self.flights_start[i], self.flights_start[i+1]])
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
            month = '0' + (hex(ord(header[14])))[2:] if len((hex(ord(header[14])))[2:]) == 1 else (hex(ord(header[14])))[2:]
            day = '0' + (hex(ord(header[13])))[2:] if len((hex(ord(header[13])))[2:]) == 1 else (hex(ord(header[13])))[2:]
            hour = '0' + (hex(ord(header[11])))[2:] if len((hex(ord(header[11])))[2:]) == 1 else (hex(ord(header[11])))[2:]
            minute = '0' + (hex(ord(header[10])))[2:] if len((hex(ord(header[10])))[2:]) == 1 else (hex(ord(header[10])))[2:]
            second = '0' + (hex(ord(header[9])))[2:] if len((hex(ord(header[9])))[2:]) == 1 else (hex(ord(header[9])))[2:]
            start_date = datetime.datetime(int(year), int(month), int(day),
                                           int(hour), int(minute), int(second))
            self.start_date.append(start_date)

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
            #duration_sec = time.strftime('%H h %M m %S s', time.gmtime(duration_time))
            self.durations.append(duration_time)
            #self.durations_int.append(duration_time)
        #------ Calculate duration for last flight ---------
        last_dur = self.flight_intervals[-1][1] - self.flight_intervals[-1][0]  # Bytes
        dur = (last_dur / self.frame_len) * self.frame_duration
        #duration_sec = time.strftime('%H h %M m %S s', time.gmtime(dur))
        #self.durations.append(duration_sec)
        self.durations.append(dur)
        #self.durations_int.append(dur)

    def get_flights_end(self):
        i = 0
        while i < len(self.start_date):
            flight_end = self.start_date[i] + datetime.timedelta(seconds=int(self.durations[i]))
            self.end_date.append(flight_end)
            i += 1