
import binascii
import os
import struct
"""this module:
- finds ARINC 717 synchrowords
- checks integrity of frames
- return only valid frames"""

FRAME_SIZE = 3072
DISTANCE = 768


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
            length = self.end - self.start
            self.flight = data.read(length)

    def make_flight(self):
        if "flight" in self.name:
            """make tmp file for future processing"""
            separator = self.path.rfind('/')
            new_path = self.path[:separator + 1]
            file_name = new_path + str(self.name)
            param_file_name = file_name + ".inf"  # target parametric file/mix scheme is applied
            tmp_param_file = file_name + ".bin"  # interim file with parametric data
            tmp_file_name = file_name + ".tmp"  # tmp file with flight
            new_file = open(tmp_file_name, 'wb')
            new_file.write(self.flight)
            """depending on QAR type -> send to proper class"""
            saab = SAAB(tmp_file_name, param_file_name, tmp_param_file)
        elif "raw" in self.name:
            """save raw data in file"""
            separ = self.path.rfind('/')
            new_path = self.path[:separ + 1]
            new_file = open(new_path + str(self.name) + '.bin', 'wb')
            new_file.write(self.flight)


class SAAB(object):

    def __init__(self, tmp_file_name, param_file_name, tmp_param_file):
        self.param_file = open(param_file_name, "wb")  # target parametric file ".inf"
        self.tmp_param_file = open(tmp_param_file, "wb")  # tmp file with parametric data
        #self.parameters = (open(tmp_file_name, "rb")).read()
        self.frame_len = 384  # bytes in frame
        self.subframe_len = 96  # bytes in subframe
        self.sw_one = "001001000111"  # syncword one
        self.sw_two = "010110111000"  # syncword two

        self.export_param_saab(tmp_file_name, tmp_param_file)

    def export_param_saab(self, tmp_file_name, tmp_param_file):
        #--------write header to target parametric file------------
        #self.param_file.write(self.data.read(128))
        data = (open(tmp_file_name, "rb")).read()  # flight
        self.tmp_param_file.write(data[:128])
        #self.param_file.write(data[:128])
        i = 128  # start after header
        #j = 0  # counter of recorded bytes
        #-------each byte after FF is a parametric byte----
        #-------so we need to write only them--------------
        #while i < (os.stat(tmp_file_name)).st_size - 1:
        while i < len(data) - 1:
            if ord(data[i]) == 255:
                self.tmp_param_file.write(data[i + 1])
                i += 2  # not to read byte that has been already read
                #j += 1
            else:
                i += 1
        self.tmp_param_file.close()
        self.scheme_search(tmp_param_file)


    def scheme_search(self, tmp_param_file):
        param_file_start = 0
        param_file_end = (os.stat(tmp_param_file)).st_size
        source_file = (open(tmp_param_file, "rb")).read()
        self.param_file.write(source_file[:128])
        self.bytes_counter = 128
        found_sw = False  # indicator of found/not found syncword
        #---------four bytes, in which we search for syncword----
        search_bytes = [source_file[self.bytes_counter],
                        source_file[self.bytes_counter + 1],
                        source_file[self.bytes_counter + 2]]
        self.bytes_counter += 3
        mix_type = None

        while not found_sw and self.bytes_counter < param_file_end:
            next_byte = source_file[self.bytes_counter]
            self.bytes_counter += 1
            search_bytes.append(next_byte)  # append fourth byte
            mixed_words = self.mix_syncword(search_bytes)  # send them to check for scheme

            if mixed_words is None:
                break
            del search_bytes[0]  # remove first byte -> ensure shift by byte

            i = 0
            for word in mixed_words:
                if word == self.sw_one:
                    print("found match")
                    print(self.bytes_counter)
                    frame = source_file[self.bytes_counter:self.bytes_counter + self.frame_len]
                    self.bytes_counter += self.frame_len
                    next_frame_search = [frame[self.frame_len - 4],
                                         frame[self.frame_len - 3],
                                         frame[self.frame_len - 2],
                                         frame[self.frame_len - 1]]
                    next_subframe_search = [frame[self.subframe_len - 4],
                                            frame[self.subframe_len - 3],
                                            frame[self.subframe_len - 2],
                                            frame[self.subframe_len - 1]]
                    frame_sw_variants = self.mix_syncword(next_frame_search)
                    subframe_sw_variants = self.mix_syncword(next_subframe_search)

                    if frame_sw_variants[i] == self.sw_one and subframe_sw_variants[i] == self.sw_two:
                        print("found mix type")
                        found_sw = True
                        #source_file.seek(-(len(frame) + 4), 1)
                        self.bytes_counter -= (self.frame_len +4)
                        mix_type = i
                        print("mix type is # %s"%mix_type)
                    else:
                        self.bytes_counter -= self.frame_len
                        #source_file.seek(-(len(frame)), 1)
                else:
                    i += 1

        if mix_type is None:
            #-------cases when flight is too small------
            #-------about few min/less than 10 min------
            self.param_file.close()
            print("didnt find syncword")
        elif mix_type % 2 == 1:
            #----if syncword is found at 2d subword-----
            #----it means that syncowrd is at the ------
            #----end of list (2d, 3d bytes)-------------
            #----so we shift two byes and --------------
            #----can use the same scheme but for first subword------
            mix_type -= 1
            extract_syncword = [source_file[self.bytes_counter], source_file[self.bytes_counter + 1],
                                source_file[self.bytes_counter + 2], source_file[self.bytes_counter + 3]]
            syncword_first = self.mix_words(extract_syncword, mix_type)
            #source_file.seek(-1, 1)
            self.bytes_counter += 3

            for each in syncword_first[2:]:  # take the last two byte which contain syncword
                sw_part = int(each, 2)
                sw_to_write = (struct.pack("i", sw_part))[:1]
                self.param_file.write(sw_to_write)

        j = self.bytes_counter
        while j < param_file_end - 3:
            four_bytes_to_mix = [source_file[self.bytes_counter], source_file[self.bytes_counter + 1],
                                source_file[self.bytes_counter + 2], source_file[self.bytes_counter + 3]]
            j += 4
            mixed_words = self.mix_words(four_bytes_to_mix, mix_type)
            #source_file.seek(-1, 1)
            self.bytes_counter += 3
            j -= 1
            for each in mixed_words:
                value = int(each, 2)  # convert binary string to int
                to_write = (struct.pack("i", value))[:1]  # int takes 4 byte, but we need only first
                # as the rest are 0s in our case, because we supply only 8 bits (one byte)
                self.param_file.write(to_write)

    def mix_syncword(self, four_bytes):
        bin_str = ""
        mixed_words = []  # 8 items list
        byte_size = 8
        for byte in four_bytes:
            #-----convert byte to binary representation---------
            #-----exclude "0b" at start and fill with ----------
            #-----zeros at the beginning to make 8 symbols------
            bin_str += ((bin(ord(byte)))[2:]).zfill(byte_size)

        #------type one |3|5|8|7|1|------------
        mixed_words.append(bin_str[23:24] + bin_str[8:16] + bin_str[:3])  # 0 index/first subword
        mixed_words.append(bin_str[27:32] + bin_str[16:23])  # 1 index/second subword

        #------type two |5|3|1|7|8|------------
        mixed_words.append(bin_str[9:16] + bin_str[:5])  # 2 index/first subword
        mixed_words.append(bin_str[29:32] + bin_str[16:24] + bin_str[8:9])  # 3 index/second subword

        #------type three |8|4|4|8|------------
        mixed_words.append(bin_str[12:16] + bin_str[:8])  # 4 index/first subword
        mixed_words.append(bin_str[16:24] + bin_str[8:12])  # 5 index/second subword

        #------type four |6|2|2|6|8|------------
        mixed_words.append(bin_str[10:16] + bin_str[:6])  # 6 index/first subword
        mixed_words.append(bin_str[30:32] + bin_str[16:24] + bin_str[8:10])  # 7 index/second subword

        return mixed_words


    def mix_words(self, bytes_to_mix, mix_type):
        middle = self.mix_syncword(bytes_to_mix)
        tmp_str_1 = "0000" + middle[mix_type]
        tmp_str_2 = "0000" + middle[mix_type + 1]
        mixed_words = [tmp_str_1[8:16], tmp_str_1[0:8],
                       tmp_str_2[8:16], tmp_str_2[0:8]]
        return mixed_words












