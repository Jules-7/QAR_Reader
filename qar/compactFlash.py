#-*-coding: utf-8-*-
import os
from specific_header_types import HeaderType32Bytes

SAVE_OPTION = "__save__"


class CompactFlash(HeaderType32Bytes):

    def __init__(self, path, qar_type):
        HeaderType32Bytes.__init__(self, path, qar_type)
        self.frame_len = 768  # Bytes
        self.cluster_size = 8192
        self.frame_duration = 2  # sec
        self.compact_flash_size = 500400*512  # 512MB
        if SAVE_OPTION in path:
            sep_path = path.find(SAVE_OPTION)
            self.path = path[:sep_path]
            self.path_save = path[sep_path+len(SAVE_OPTION):]
            transformed_path = r"\\.\%s" % self.path[:2]
            self.dat = file(transformed_path, "rb")
            #------------------------------------------------------------
            #------ Copy data from compact flash into tmp file on desktop
            #------------------------------------------------------------
            copy_file = self.copy_cf_data()
            self.source = open(copy_file, "rb")
            self.source_len = os.stat(copy_file).st_size
            # re-assignment due to use os self.path for future processing
            self.path = copy_file
        else:
            self.path = path
            self.source = open(self.path, "rb")
            self.source_len = os.stat(self.path).st_size
        #-------------------------------------------------------
        #------ Search for flights start -----------------------
        #-------------------------------------------------------
        self.find_start()
        self.find_flights()
        self.get_flight_intervals()
        self.get_flights_start()
        self.get_flights_duration()
        self.get_flights_end()


class B767QARFlights(HeaderType32Bytes):

    def __init__(self, path, qar_type):
        HeaderType32Bytes.__init__(self, path, qar_type)
        self.frame_len = 1536  # Bytes
        self.cluster_size = 8192
        self.frame_duration = 4  # sec
        self.path = path
        self.source = open(self.path, "rb")
        self.source_len = os.stat(self.path).st_size
        #-------------------------------------------------------
        #------ Search for flights start -----------------------
        #-------------------------------------------------------
        self.find_start()
        self.find_flights()
        self.get_flight_intervals()
        self.get_flights_start()
        self.get_flights_duration()
        self.get_flights_end()


class B737QARNG(HeaderType32Bytes):

    """ 1. Find 0403 header
        2. Find end of flight - 64 bytes of 00
        3. Find next 0403 header
        4. Find end of flight - 64 bytes of 00
        ...
    """

    def __init__(self, path, qar_type):
        HeaderType32Bytes.__init__(self, path, qar_type)
        self.frame_len = 1536  # Bytes
        self.cluster_size = 8192
        self.frame_duration = 4  # sec
        self.path = path
        self.flights_end = []
        self.source = open(self.path, "rb")
        self.source_len = os.stat(self.path).st_size
        self.clusters = range(0, self.source_len, self.cluster_size)
        #-------------------------------------------------------
        #------ Search for flights start -----------------------
        #-------------------------------------------------------
        #self.find_start()
        self.find_flights()
        self.get_flight_intervals()
        self.get_flights_start()
        self.get_flights_duration()
        self.get_flights_end()

    # def find_start(self):
    #     while self.bytes_counter < self.source_len - self.cluster_size:
    #         flights_start = self.find_syncword()
    #         if flights_start:
    #             break

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
                #flight = self.headers[0][3]
                #flight_num = int('0' + (hex(ord(flight)))[2:])
                #self.current_flight = flight_num
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
        while self.bytes_counter < self.source_len - self.cluster_size - 16:
            if not self.flights_start:
                self.find_start()
            else:
                for cluster in self.clusters:
                    if cluster >= self.bytes_counter:
                        next_start = cluster
                        self.flights_start.append(next_start)
                        self.source.seek(cluster, 0)
                        self.headers.append(self.source.read(self.header_len))
                        self.source.seek(-self.header_len, 1)
                        break
            self.find_end()

    def find_end(self):
        while self.bytes_counter < self.source_len - self.cluster_size - 16:
            self.bytes_counter = self.source.tell()
            next_bytes = self.source.read(512)
            next_bytes_str = ''.join([str(ord(one_byte)) for one_byte in next_bytes])
            self.bytes_counter += 512
            if "00000000000000000000000000000000" in next_bytes_str:
                self.flights_end.append(self.bytes_counter)
                break
            # try:
            #     if ord(next_byte) == 0:
            #         counter += 1
            #     else:
            #         counter = 0
            #     self.bytes_counter += 1
            #     if counter == 64:
            #         self.flights_end.append(self.bytes_counter)
            #         break
            # except TypeError:  # no more bytes with data -> empty bytes at the end
            #     break

    def get_flight_intervals(self):
        i = 0
        for each in self.flights_start:
            try:
                self.flight_intervals.append([self.flights_start[i],self.flights_end[i]])
            except IndexError:
                self.flight_intervals.append([self.flights_start[i],
                                              self.get_last_flight_end(self.flights_start[i])])
            i += 1