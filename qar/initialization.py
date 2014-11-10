#-*-coding: utf-8-*-
import time
import datetime
import os
import struct
import stat
#from os import stat

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

--------------------------
| Name      | Identifier |
--------------------------
| QAR-12    | 0          |
| QAR-64    | 1          |
| QAR-T-M   | 5          |
| QAR-T-L   | 6          |
| QAR-B-1   | 10         |
| QAR-B-3   | 11         |
| QAR-T-2   | 14         |
| CFDR-42   | 21         |
| QAR-SARPP | 22         |
| VDR       | 254        |
| QAR-P     | 255        |
--------------------------
"""


class Initialize(object):

    def __init__(self, path, qar_type, date, time_val, flight, qar_n):
        self.cluster_size = 32 * 1024  # 32KB
        self.sector_size = 512  # Bytes
        self.path = path
        self.qar_type = qar_type
        self.date = date
        self.time = time_val
        #self.switchboard = switchboard  # Number of switchboard for QAR-12
        self.qar_n = int(str(qar_n))  # number of QAR
        print(self.qar_n)
        self.flight = flight  # flight number
        self.clu_2_size = 32768 / 2  # bytes -> one cluster
        self.clu_3_size = 1015234560  # bytes
        self.clu_2 = self.path + "CLU_0002.dat"
        self.clu_3 = self.path + "CLU_0003.dat"
        self.get_day_time()
        self.write_header()
        #self.clear_clu_3()

    #def check_path(self):
        #check_clu_2 = os.path.isfile(self.clu_2)
        #check_clu_3 = os.path.isfile(self.clu_3)
        #print(check_clu_3), check_clu_2

    def get_day_time(self):
        print(self.date)
        print(self.time)
        #day_time = datetime.datetime.now()

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

        qars = {'A320 - QAR': [255, 1],
                'A320 - Compact Flash': [3, 1/2],
                'B747 - QAR': [7, 1/4],
                'An148 - BUR-92': [13, 1],
                'QAR-4XXX': [254, 1]}
        os.chmod(self.clu_2, stat.S_IRWXU)  # change mode for writing
        dat_2 = open(self.clu_2, "wb")
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
        qar_type = int(str((qars[self.qar_type])[0]))
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
        frame_frequency = str((qars[self.qar_type])[1])
        print(frame_frequency)
        data_for_header.append((str(bin(ord(frame_frequency)))[2:]).rjust(8, "0"))

        #----- 18 empty bytes ----
        i = 0
        while i < 16:
            data_for_header.append("0")
            i += 1

        #----- qar_number -----
        qar_number = (str(bin(self.qar_n))[2:]).rjust(8, "0")
        data_for_header.append(qar_number)

        #----- year --------
        value = bin(1)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- month ------
        value = bin(2)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- day ------
        value = bin(3)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- hour -----
        value = bin(4)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- minute ----
        value = bin(5)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- sec ------
        value = bin(6)
        data_for_header.append(value)
        data_for_header.append("0")

        #----- 64 empty bytes ----
        i = 0
        while i < 64:
            data_for_header.append("0")
            i += 1

        data = [str(each) for each in data_for_header]

        for each in data:
            print(each)
            dat_int = int(each, 2)
            dat_write = (struct.pack("i", dat_int))[:1]
            dat_2.write(dat_write)
        dat_2.close()

    def clear_clu_3(self):
        start = time.clock()
        byte_counter = 0
        os.chmod(self.clu_3, stat.S_IWRITE)  # change mode for writing
        #fd = os.open(self.clu_3, os.O_RDWR|os.O_CREAT )
        dat_3 = open(self.clu_3, "wb")
        zeros = (struct.pack("i", 0))
        while byte_counter <= self.clu_3_size:
            #os.write(fd, zeros)
            #os.ftruncate(fd, 10)
            dat_3.write(zeros)
            byte_counter += 4
        end = time.clock()
        print(end-start)
        # Open a file


