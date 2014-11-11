#-*-coding: utf-8-*-
import datetime
import os
import struct
import stat
import time

"""
          HEADER DESCRIPTION

--------------------------------------------------------------------
| Shift     (address)  |bytes N |       Description                |
--------------------------------------------------------------------
| 0-7       (0x00)     |   8    |MONSTR00                          |
| 8-9       (0x07)     |   2    |0x55AA-input, 0xAA55-input        |
| 10        (0x0a)     |   1    |QAR type                          |
| 11        (0x0b)     |   1    |dimension (1-bits, 0-bytes)       |
| 12-13     (0x0c-0x0d)|   2    |channel size (in dimension units) |
| 14-15     (0x0e-0x0f)|   2    |frame size (in channels)          |
| 16-17     (0x10-0x11)|   2    |frames frequency (in seconds)     |
| 18-33     (0x12-0x21)|   2*8  |conversion mask                   |
| 34-35     (0x22-0x23)|   2    |switchboard N                     |
| 36-37     (0x24-0x25)|   2    |QAR N                             |
| 38-39     (0x26-0x27)|   2    |year (binary decimal)             |
| 40-41     (0x28-0x29)|   2    |month (binary decimal)            |
| 42-43     (0x2a-0x2b)|   2    |day (binary decimal)              |
| 44-45     (0x2c-0x2d)|   2    |hours (binary decimal)            |
| 46-47     (0x2e-0x2f)|   2    |minutes (binary decimal)          |
| 48-49     (0x30-0x31)|   2    |seconds (binary decimal)          |
| 50-51     (0x32-0x33)|   2    |processing code                   |
| 52-53     (0x34-0x35)|   2    |flight N                          |
| 54        (0x36)     |   1    |firmware version                  |
| 55-111    (0x37-0x6f)|   1*57 |not being used                    |
| 112-115   (0x70-0x73)|   4    |processor timer reference value   |
| 116-119   (0x74-0x77)|   4    |not being used                    |
| 120-123   (0x78-0x7b)|   4    |processor timer                   |
| 124-127   (0x7c-0x7f)|   4    |not being used                    |
--------------------------------------------------------------------

    QAR types

-----------------------------
| Name         | Identifier |
-----------------------------
| QAR-12       | 0          |
| QAR-64       | 1          |
| QAR-T-M      | 5          |
| QAR-T-L      | 6          |
| QAR-B-1      | 10         |
| QAR-B-3      | 11         |
| QAR-T-2      | 14         |
| CFDR-42      | 21         |
| QAR-SARPP    | 22         |
| VDR          | 254        |
| QAR-P        | 255        |
-----------------------------
| A320-CF      | 70         |
| B747-QAR     | 71         |
| An148-BUR-92 | 72         |
| QAR-2100     | 73         |
| QAR-4100     | 74         |
| QAR-4120     | 75         |
| QAR-4700     | 76         |
-----------------------------
"""

monstr = 'MONSTR'



class Initialize(object):

    def __init__(self, path, qar_type, date, time_val, flight_n, qar_n):
        self.cluster_size = 32 * 1024  # 32KB
        self.sector_size = 512  # Bytes
        self.path = path
        self.qar_type = qar_type
        self.date = date
        self.time = time_val
        #self.switchboard = switchboard  # Number of switchboard for QAR-12
        self.qar_n = qar_n  # number of QAR
        self.flight_n = flight_n  # flight number
        self.clu_2_size = 32768 / 2  # bytes -> one cluster
        self.clu_3_size = 1015234560  # bytes
        self.clu_2 = self.path + "CLU_0002.dat"
        self.clu_3 = self.path + "CLU_0003.dat"
        self.qars = {'A320 - QAR':           [255, 1],
                     'SAAB':                 [254, 1],
                     'A320 - Compact Flash': [70, 1/2],
                     'B747 - QAR':           [71, 1/4],
                     'An148 - BUR-92':       [72, 1],
                     'QAR-2100':             [73, 1],
                     'QAR-4100':             [74, 1],
                     'QAR-4120':             [75, 1],
                     'QAR-4700':             [76, 1]}
        self.headers = []
        self.get_day_time()
        self.get_qar_and_flight()
        self.get_frame_frequency()
        self.check_path()
        self.write_header()


    def check_path(self):
        check_clu_2 = os.path.isfile(self.clu_2)
        if not check_clu_2:
            clu_2 = open(self.clu_2, "w+")
            clu_2.close()
        check_clu_3 = os.path.isfile(self.clu_3)
        if not check_clu_3:
            start = time.clock()
            with open(self.clu_3, "wb") as clu_3:
                clu_3.truncate(self.clu_3_size)
            end = time.clock()
            print(end - start)
        else:
            with open(self.clu_3, "r+") as self.dat:
                self.index = 0
                self.file_len = os.stat(self.clu_3).st_size
                self.find_flights()
                self.clear_clu_3()

    def get_day_time(self):
        self.year = datetime.datetime.strftime(self.date, "%y")
        self.month = datetime.datetime.strftime(self.date, "%m")
        self.day = datetime.datetime.strftime(self.date, "%d")
        self.hour = datetime.datetime.strftime(self.date, "%H")
        self.minute = datetime.datetime.strftime(self.date, "%M")
        self.second = datetime.datetime.strftime(self.date, "%S")

    def get_qar_and_flight(self):
        if self.qar_n:
            self.qar = self.qar_n
        else:
            self.qar_n = 0
            self.qar = self.qar_n
        if self.flight_n:
            self.flight = self.flight_n
        else:
            self.flight_n = 0
            self.flight = self.flight_n

    def get_hex_repr(self, value):
        hex_value = '0x%s' % value
        int_value = int(hex_value, 16)
        bin_value = bin(int_value)
        return bin_value

    def get_frame_frequency(self):
        frequency = self.qars[self.qar_type][1]
        self.frequency = self.get_hex_repr(frequency)

    def write_header(self):
        qar_types = {0: [u"ЭБН-12", ],
                     1: [u"ЭБН-64", ],
                     5: u"ЭБН-Т-М",
                     6: u"ЭБН-Т-Л",
                     10: u"ЭБН-Б-1",
                     11: u"ЭБН-Б-3",
                     14: u"ЭБН-Т-2",
                     21: u"CFDR-42",
                     22: u"ЭБН САРПП",
                     254: [u"VDR", 1],
                     255: [u"ЭБН-Р", 1]}

        os.chmod(self.clu_2, stat.S_IWRITE)  # change mode for writing

        with open(self.clu_2, "wb") as dat_2:
            data_for_header = []

            #----- monstr word ------
            monstr = "MONSTR00"
            monstr_word = [(str(bin(ord(each)))[2:]).rjust(8, "0") for each in monstr]
            for each in monstr_word:
                data_for_header.append(each)

            #----- 9-10 bytes ------
            data_for_header.append("0")
            data_for_header.append("0")

            #----- qar_type ------
            qar_type = int(str((self.qars[self.qar_type])[0]))
            qar = (str(bin(qar_type))[2:]).rjust(8, "0")
            data_for_header.append(str(qar))

            #----- dimension -------
            data_for_header.append("0")

            #----- channel size -----
            data_for_header.append("0")
            data_for_header.append("0")

            #----- frame size -------
            data_for_header.append("0")
            data_for_header.append("0")

            #---- frame frequency ----
            data_for_header.append("0")
            data_for_header.append(self.frequency)

            #----- 18 empty bytes ----
            i = 0
            while i < 18:
                data_for_header.append("0")
                i += 1

            #----- qar_number -----
            qar_bin = self.get_hex_repr(self.qar)
            data_for_header.append(qar_bin)
            data_for_header.append("0")

            #----- year --------
            year_bin = self.get_hex_repr(self.year)
            data_for_header.append(year_bin)
            data_for_header.append("0")

            #----- month ------
            month_bin = self.get_hex_repr(self.month)
            data_for_header.append(month_bin)
            data_for_header.append("0")

            #----- day ------
            day_bin = self.get_hex_repr(self.day)
            data_for_header.append(day_bin)
            data_for_header.append("0")

            #----- hour -----
            hour_bin = self.get_hex_repr(self.hour)
            data_for_header.append(hour_bin)
            data_for_header.append("0")

            #----- minute ----
            minute_bin = self.get_hex_repr(self.minute)
            data_for_header.append(minute_bin)
            data_for_header.append("0")

            #----- sec ------
            second_bin = self.get_hex_repr(self.second)
            data_for_header.append(second_bin)
            data_for_header.append("0")

            data_for_header.append("0")
            data_for_header.append("0")

            #----- flight number ------
            flight_bin = self.get_hex_repr(self.flight)
            data_for_header.append(flight_bin)
            data_for_header.append("0")

            #----- 74 empty bytes ----
            i = 0
            while i < 74:
                data_for_header.append("0")
                i += 1

            data = [str(each) for each in data_for_header]

            for each in data:
                dat_int = int(each, 2)
                dat_write = (struct.pack("i", dat_int))[:1]
                dat_2.write(dat_write)

    def clear_clu_3(self):
        """ Clearing means overwrite only first byte of each header with 0,
        so it won`t be found during search """
        os.chmod(self.clu_3, stat.S_IWRITE)  # change mode for writing
        # in case of using r+ mode it is possible to overwrite only specific bytes
        # in case of wb mode -> it will write necessary bytes, fill in other with zeros
        # and after last written byte (last specified to be written) will truncate file
        with open(self.clu_3, "r+") as dat_3:
            source_data = int(self.get_hex_repr(0), 2)
            for each in self.headers:
                dat_3.seek(each, 0)
                data = struct.pack("i", source_data)
                dat_3.write(data)

    def format_clu_3(self):
        """ Formatting clears file -> fill whole file with zeros
        This process takes about 40 min """
        byte_counter = 0
        os.chmod(self.clu_3, stat.S_IWRITE)  # change mode for writing
        dat_3 = open(self.clu_3, "wb")
        zeros = (struct.pack("i", 0))
        while byte_counter <= self.clu_3_size:
            dat_3.write(zeros)
            byte_counter += 4

    def is_flight(self):
        ''' check for MONSTR and if so capture header index '''
        flight = self.dat.read(6)
        if flight == monstr:
            self.headers.append(self.index)
        self.index += self.cluster_size

    def find_flights(self):
        ''' find all flights indexes '''
        while self.index < self.file_len:
            if self.index == 524288:
                self.dat.seek(524288)
                self.is_flight()
            else:
                self.dat.seek(self.index)
                self.is_flight()
