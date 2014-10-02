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
                    #counter += 16
                    break
                else:
                    counter += 1
                    part = part[1:]
            data.seek(self.start)
            length = counter
            self.flight = data.read(length)
        else:
            data.seek(self.start)
            print("start index is at %s"%data.tell())
            length = self.end - self.start
            print("length of flight is %s in bytes"%length)
            self.flight = data.read(length)
            print("length of flight piece that has been read is %s"%len(self.flight))

    def make_flight(self):
        if "flight" in self.name:
            """make tmp file for future processing"""
            separator = self.path.rfind('/')
            new_path = self.path[:separator + 1]
            file_name = new_path + str(self.name)
            param_file_name = file_name + ".inf"
            print("param_file_name is %s"%param_file_name)
            tmp_file_name = file_name + ".tmp"
            print("tmp_file_name is %s"%tmp_file_name)
            new_file = open(tmp_file_name, 'wb')
            new_file.write(self.flight)
            saab = SAAB(tmp_file_name, param_file_name)
            #self.export_param_saab()

            """depending on QAR type -> send to proper method"""
            #self.export_param_saab(tmp_file, new_path)

        elif "raw" in self.name:
            """save raw data in file"""
            separ = self.path.rfind('/')
            new_path = self.path[:separ + 1]
            #self.status = 40
            new_file = open(new_path + str(self.name) + '.bin', 'wb')
            new_file.write(self.flight)


class SAAB(object):

    def __init__(self, tmp_file_name, param_file_name):
        self.data = open(tmp_file_name, "rb")#flight  #data of flight
        self.param_file = open(param_file_name, "wb")  #target parametric file ".inf"
        self.frame_len = 384  # bytes in frame
        self.subframe_len = 96  # bytes in subframe
        self.sw_one = "001001000111"  # syncword one
        self.sw_two = "010110111000"  # syncword two

        self.export_param_saab(tmp_file_name)

    def export_param_saab(self, tmp_file_name):
        print("flight length is %s"%(os.stat(tmp_file_name)).st_size)
        parameters = open(tmp_file_name + ".bin", "wb")
        print("parameters file name is %s"%parameters)
        #--------write header to target parametric file------------
        #self.param_file.write(self.data.read(128))
        parameters.write(self.data.read(128))
        i = 128  # start after header
        #-------each byte after FF is a parametric byte----
        #-------so we need to write only them--------------
        while i < (os.stat(tmp_file_name)).st_size - 1:
            if ord(self.data.read(1)) == 255:
                #print(ord(self.data.read(1)))
                parameters.write(self.data.read(1))
                i += 2  #not to read byte that has been already read
            else:
                #self.data.seek(-1, 1)
                i += 1
        print("i equals to %s"%i)
        print("tmp_file_size is %s"%(os.stat(tmp_file_name + ".bin")).st_size)
        parameters.close()
        self.scheme_search(tmp_file_name + ".bin")

    def scheme_search(self, tmp_file_name):
        param_file_start = 0
        param_file_end = (os.stat(tmp_file_name)).st_size
        source_file = open(tmp_file_name, "rb")
        found_sw = False  # indicator of found/not found syncword
        #---------four bytes, in which we search for syncword----
        search_bytes = [source_file.read(1),
                        source_file.read(1),
                        source_file.read(1)]
        self.bytes_counter = 3
        mix_type = None

        while not found_sw or self.bytes_counter == param_file_end:
            next_byte = source_file.read(1)
            self.bytes_counter += 1
            search_bytes.append(next_byte)  # append fourth byte
            mixed_words = self.mix_syncword(search_bytes)  # send them to check for scheme
            del search_bytes[0]  # remove first byte -> ensure shift by byte

            i = 0
            for word in mixed_words:
                if word == self.sw_one:
                    frame = source_file.read(self.frame_len)
                    next_frame_search = [frame[len(frame) - 4],
                                         frame[len(frame) - 3],
                                         frame[len(frame) - 2],
                                         frame[len(frame) - 1]]
                    next_subframe_search = [frame[self.subframe_len - 4],
                                            frame[self.subframe_len - 3],
                                            frame[self.subframe_len - 2],
                                            frame[self.subframe_len - 1]]
                    frame_sw_variants = self.mix_syncword(next_frame_search)
                    subframe_sw_variants = self.mix_syncword((next_subframe_search))

                    if frame_sw_variants[i] == self.sw_one and subframe_sw_variants[i] == self.sw_two:
                        print("found mix type")
                        found_sw = True
                        source_file.seek(-(len(frame) + 4), 1)
                        mix_type = i
                        print("mix type is # %s"%mix_type)
                    else:
                        source_file.seek(-(len(frame)), 1)
                else:
                    i += 1


    def mix_syncword(self, four_bytes):
        bin_str = ""
        mixed_words = []  # 8 items list
        byte_size = 8
        for byte in four_bytes:
            #-----convert byte to binary representation---------
            #-----exclude "0b" at start and fill with ----------
            #-----zeros at the beginning to make 8 symbols------
            try:
                bin_str += ((bin(ord(byte)))[2:]).zfill(byte_size)
            except:
                print(self.bytes_counter)
                break
        #------type one |3|5|8|7|1|------------
        mixed_words.append(bin_str[23:24] + bin_str[8:16] + bin_str[:3])  # 0 index/first syncword
        mixed_words.append(bin_str[27:32] + bin_str[16:23])  # 1 index/second syncword

        #------type two |5|3|1|7|8|------------
        mixed_words.append(bin_str[9:16] + bin_str[:5])  # 2 index/first syncword
        mixed_words.append(bin_str[29:32] + bin_str[16:24] + bin_str[8:9])  # 3 index/second syncword

        #------type three |8|4|4|8|------------
        mixed_words.append(bin_str[12:16] + bin_str[:8])  # 4 index/first syncword
        mixed_words.append(bin_str[16:24] + bin_str[8:12])  # 5 index/second syncword

        #------type four |6|2|2|6|8|------------
        mixed_words.append(bin_str[10:16] + bin_str[:6])  # 6 index/first syncword
        mixed_words.append(bin_str[30:32] + bin_str[16:24] + bin_str[8:10])  # 7 index/second syncword

        return mixed_words













