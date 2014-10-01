import binascii
import os
"""this module:
- finds ARINC 717 synchrowords
- checks integrity of frames
- return only valid frames"""
FRAME_SIZE = 3072
DISTANCE = 768

'''
#BIN DIRECT
synch_word_1 = '111000100100'
synch_word_2 = '000111011010'
synch_word_3 = '111000100101'
synch_word_4 = '000111011011'
'''

#HEX DIRECT
s1 = 'e24'
s2 = '1da'
s3 = 'e25'
s4 = '1db'

'''
#HEX REVERSE
s1 = '247'
s2 = '5b8'
s3 = 'a47'
s4 = 'db8'
'''


class Flight:

    """this class takes start and end indexes of flight
    and make either RAW file or send data further
    to be processed according to QAR type"""

    def __init__(self, start, end, path, name):
        self.start = start
        self.end = end
        self.path = path
        self.name = name
        self.get_flight()
        self.make_flight()

    def get_flight(self):
        header = 128
        eof = [255] * 16
        data = open(self.path, 'rb')
        if self.end == 0:
            data.seek(self.start + header)
            counter = header
            dat = data.read(15)
            part = [ord(each) for each in dat]
            #print(str_part)
            while True:
                part.append(ord(data.read(1)))
                if part == eof:
                    counter += 16
                    break
                else:
                    counter += 1
                    part = part[1:]
            data.seek(self.start)
            length = counter
            self.flight = data.read(length)
        else:
            data.seek(self.start)
            length = self.end - self.start
            self.flight = data.read(length)

    def make_flight(self):
        if "flight" in self.name:
            """make tmp file for future processing"""
            separ = self.path.rfind('/')
            new_path = self.path[:separ + 1]
            tmp_file = new_path + str(self.name) + '.tmp'
            new_file = open(tmp_file, 'wb')
            self.export_param_saab(self.flight, new_file)
            #new_file.write(self.flight)
            """depending on QAR type -> send to proper method"""
            #self.export_param_saab(tmp_file, new_path)

        elif "raw" in self.name:
            """save raw data in file"""
            separ = self.path.rfind('/')
            new_path = self.path[:separ + 1]
            #self.status = 40
            new_file = open(new_path + str(self.name) + '.bin', 'wb')
            new_file.write(self.flight)

    def export_param_saab(self, data, new_file):
        #--------write header------------
        new_file.write(data[:128])
        i = 128
        while i < len(data):
            if ord(data[i]) == 255:
                new_file.write(data[i + 1])
            i += 1
        new_file.close()
        self.check_saab(new_file)

    def check_saab(self, path):
        file_start = 0
        file_end = (os.stat(path)).st_size
        frame_length = 384
        subframe_length = 96
        syncword_one = "001001000111"
        syncword_two = "010110111000"
        byte_counter = 0
        initial_four_byte_words = []
        temp_data_file = open(path, "rb")
        bit_sting = ""




'''
        norm_word = []
        bit_string = ""
        byte_size = 8

        for each in words:
            bit_string += ((bin(ord(each)))[2:]).zfill(byte_size)

        #------type one |3|5|8|7|1|------------
        norm_word.append(bit_string[23:24] + bit_string[8:16] +
                             bit_string[:3])  # 0 index/first syncword
        norm_word.append(bit_string[27:32] +
                             bit_string[16:23])  # 1 index/second syncword

        #------type two |5|3|1|7|8|------------
        norm_word.append(bit_string[9:16] +
                             bit_string[:5])  # 2 index/first syncword
        norm_word.append(bit_string[29:32] + bit_string[16:24] +
                             bit_string[8:9])  # 3 index/second syncword

        #------type three |8|4|4|8|------------
        norm_word.append(bit_string[12:16] +
                             bit_string[:8])  # 4 index/first syncword
        norm_word.append(bit_string[16:24] +
                             bit_string[8:12])  # 5 index/second syncword

        #------type four |6|2|2|6|8|------------
        norm_word.append(bit_string[10:16] +
                             bit_string[:6])  # 6 index/first syncword
        norm_word.append(bit_string[30:32] + bit_string[16:24] +
                             bit_string[8:10])  # 7 index/second syncword

        return norm_word
'''






'''
class Arinc():

    """this class takes flight indexes(path to tmp file)
    and return flight in format corresponding to QAR type"""

    def __init__(self, path):
        self.path = path
        self.data = open(self.path, "rb")
        self.sequence = ''
        self.look_for_packet()
        #self.write_txt_data()

    def look_for_packet(self):
        counter = 0
        while True:
            data = self.data.read(3)
            counter += 3
            self.sequence += binascii.hexlify(data)
            if s1 in self.sequence:
                print('counter')
            else:
                self.sequence = ''

    #def write_txt_data(self):
        #new_path = self.path.split('DAT')[0]
        #write_data = open(new_path + "txt", "w")
        #write_data.write(self.txt_data)
'''



