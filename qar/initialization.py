#-*-coding: utf-8-*-
import time
import datetime
import os
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

    def __init__(self, path, qar_type=None, switchboard=None, qar_n=None, flight=None):
        self.cluster_size = 32 * 1024  # 32KB
        self.sector_size = 512  # Bytes
        self.path = path
        self.qar_type = qar_type
        self.switchboard = switchboard  # Number of switchboard for QAR-12
        self.qar_n = qar_n  # number of QAR
        self.flight = flight  # flight number
        self.clu_2 = self.path + "CLU_0002.dat"
        self.clu_3 = self.path + "CLU_0003.dat"
        self.check_path()
        print("have rewritten files")
        self.day_time = self.get_current_day_time()
        print("today`s date and time: %s"%self.day_time)

    def check_path(self):
        check_clu_2 = os.path.isfile(self.clu_2)
        check_clu_3 = os.path.isfile(self.clu_3)
        print(check_clu_3), check_clu_2
        #if check_clu_2:
            #os.remove(self.clu_2)
        #if check_clu_3:
            #os.remove(self.clu_3)
        # ---- Create these files ---------
        #with open(self.clu_3, "rb+") as CLU_0003:
            #CLU_0003.truncate(101523460)  # bytes
        #with open(self.clu_2, "rb+") as CLU_0002:
            #CLU_0002.truncate(32768)  # bytes
        dat_2 = open(self.clu_2, "rb+")
        dat_3 = open(self.clu_3, "rb+")

    def get_current_day_time(self):
        day_time = datetime.datetime.now()
        return day_time

    def write_header(self):
        file_to_write = open(self.clu_2, "wb")
        file_to_write.write("hello")