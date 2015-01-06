import struct


class PrepareData(object):

    """ This module holds basic methods for frames search"""

    def __init__(self, tmp_file_name, param_file_name, frame_len,
                 subframe_len, progress_bar, path_to_save, flag):
        self.source_file = None
        self.param_file_end = None  # size of tmp parametric file
        # target parametric file ".inf"
        self.param_file = open(r"%s" % path_to_save + r"\\" +
                               r"%s" % param_file_name, "wb")
        self.sw_one = "001001000111"  # syncword one
        self.sw_two = "010110111000"  # syncword two
        #self.sw_two = "101001000111"  # actually its syncword three
        self.bytes_counter = 0
        self.mix_type = None
        self.frame_len = frame_len
        self.subframe_len = subframe_len  # in bytes
        self.progress_bar = progress_bar  # in bytes
        self.flag = flag

    def record_data(self):
        """ perform recording of valid frames only """
        while self.bytes_counter < self.param_file_end - 4:
            # cases when flight is too small less than 10 min
            if self.mix_type is None:
                self.param_file.close()
                print("didnt find syncword")
            elif self.mix_type % 2 == 1:
                #if syncword is found at 2d subword, it means that syncword
                #is at the end of list (2d, 3d bytes), so we shift two byes
                #and can use the same scheme but for first subword
                self.mix_type -= 1
                extract_syncword = [self.source_file[self.bytes_counter],
                                    self.source_file[self.bytes_counter + 1],
                                    self.source_file[self.bytes_counter + 2],
                                    self.source_file[self.bytes_counter + 3]]
                syncword_first = self.mix_words(extract_syncword)
                self.bytes_counter += 3
                # take the last two byte which contain syncword
                for each in syncword_first[2:]:
                    sw_part = int(each, 2)
                    sw_to_write = (struct.pack("i", sw_part))[:1]
                    self.param_file.write(sw_to_write)

                i = 0
                while i < self.frame_len - 3:
                    # read frame by 4 bytes, apply mix scheme to it and record
                    # to target file
                    # -1 byte_counter due to the fact the 12 bits words
                    words = [self.source_file[self.bytes_counter],
                             self.source_file[self.bytes_counter + 1],
                             self.source_file[self.bytes_counter + 2],
                             self.source_file[self.bytes_counter + 3]]
                    self.bytes_counter += 4
                    i += 4
                    words_mixed = self.mix_words(words)
                    self.bytes_counter -= 1
                    i -= 1
                    # take the last two byte which contain syncword
                    for each in words_mixed:
                        sw_part = int(each, 2)
                        sw_to_write = (struct.pack("i", sw_part))[:1]
                        self.param_file.write(sw_to_write)
                last_bytes = [self.source_file[self.bytes_counter],
                              self.source_file[self.bytes_counter + 1],
                              self.source_file[self.bytes_counter + 2],
                              self.source_file[self.bytes_counter + 3]]
                last_bytes_mixed = self.mix_words(last_bytes)
                # take the last two byte which contain syncword
                for each in last_bytes_mixed[:2]:
                    sw_part = int(each, 2)
                    sw_to_write = (struct.pack("i", sw_part))[:1]
                    self.param_file.write(sw_to_write)

                self.bytes_counter -= 2

            else:  # no need to change mix_type
                frame = self.source_file[self.bytes_counter:
                                         self.bytes_counter + self.frame_len + 4]
                if len(frame) < self.frame_len:  # end of data
                    break
                self.bytes_counter += self.frame_len
                self.bytes_counter -= 4
                try:
                    check_next_sw = [frame[(self.frame_len + 4) - 4],
                                     frame[(self.frame_len + 4) - 3],
                                     frame[(self.frame_len + 4) - 2],
                                     frame[(self.frame_len + 4) - 1]]
                except IndexError:  # end of data
                    break
                mixed_words = self.mix_syncword(check_next_sw)
                # perform syncword mixing according to mix scheme
                if mixed_words[self.mix_type] == self.sw_one:  # if its ok
                    i = 0
                    while i < self.frame_len:
                        next_words = [frame[i], frame[i + 1],
                                      frame[i + 2], frame[i + 3]]
                        i += 3
                        mix_next_words = self.mix_words(next_words)
                        for each in mix_next_words:
                            # convert binary string to int
                            value = int(each, 2)
                            # int takes 4 byte, but we need only first
                            to_write = (struct.pack("i", value))[:1]
                            # as the rest are 0s in our case, because
                            # we supply only 8 bits (one byte)
                            self.param_file.write(to_write)
                else:  # if its not a syncword -> search for it
                    self.bytes_counter -= self.frame_len
                    self.scheme_search()

    def header_to_param_file(self):
        header_length = None
        if self.flag == "a320_qar" or self.flag == "s340_qar" or self.flag == "b737_4700" or\
            self.flag == "b737_300_dfdr_980":
            header_length = 128  # header length is 128 bytes
        # if flag says its compact flash -> header length is 32
        elif self.flag == "a320_cf":
            header_length = 32
        # rewrite header to target file
        self.param_file.write(self.source_file[:header_length])
        self.bytes_counter += header_length  # increase counter on header size

    def scheme_search(self):
        """ Perform search of mix scheme type """
        found_sw = False  # indicator of found/not found syncword
        #---------four bytes, in which we search for syncword----
        try:
            search_bytes = [self.source_file[self.bytes_counter],
                            self.source_file[self.bytes_counter + 1],
                            self.source_file[self.bytes_counter + 2]]
        except IndexError:
            return
        self.bytes_counter += 3

        while not found_sw and self.bytes_counter < self.param_file_end:
            next_byte = self.source_file[self.bytes_counter]
            self.bytes_counter += 1
            search_bytes.append(next_byte)  # append fourth byte
            # send them to check for scheme
            mixed_words = self.mix_syncword(search_bytes)

            if mixed_words is None:
                break
            del search_bytes[0]  # remove first byte -> ensure shift by byte

            i = 0
            for word in mixed_words:
                if word == self.sw_one:
                    #----------------------------------------------------------
                    #print("found match")
                    #print(self.bytes_counter)
                    frame = self.source_file[self.bytes_counter:
                                             self.bytes_counter + self.frame_len]
                    self.bytes_counter += self.frame_len
                    try:
                        next_frame_search = [frame[self.frame_len - 4],
                                             frame[self.frame_len - 3],
                                             frame[self.frame_len - 2],
                                             frame[self.frame_len - 1]]
                    except IndexError:
                        break
                    next_subframe_search = [frame[self.subframe_len - 4],
                                            frame[self.subframe_len - 3],
                                            frame[self.subframe_len - 2],
                                            frame[self.subframe_len - 1]]
                    frame_sw_variants = self.mix_syncword(next_frame_search)
                    subframe_sw_variants = self.mix_syncword(next_subframe_search)

                    if frame_sw_variants[i] == self.sw_one and \
                            subframe_sw_variants[i] == self.sw_two:
                        found_sw = True
                        self.bytes_counter -= (self.frame_len + 4)
                        self.mix_type = i
                        #------------------------------------------------------
                        #print("found mix type")
                        #print("mix type is # %s" % self.mix_type)
                    else:
                        self.bytes_counter -= self.frame_len
                else:
                    i += 1

    def mix_syncword(self, four_bytes):
        """ Convert words by four types of mix schemes """
        bin_str = ""
        mixed_words = []  # 8 items list
        byte_size = 8
        for byte in four_bytes:
            #-----convert byte to binary representation---------
            #-----exclude "0b" at start and fill with ----------
            #-----zeros at the beginning to make 8 symbols------
            bin_str += ((bin(ord(byte)))[2:]).zfill(byte_size)

        #------type one |3|5|8|7|1|------------
        # 0 index/first subword
        mixed_words.append(bin_str[23:24] + bin_str[8:16] + bin_str[:3])
        # 1 index/second subword
        mixed_words.append(bin_str[27:32] + bin_str[16:23])

        #------type two |5|3|1|7|8|------------
        # 2 index/first subword
        mixed_words.append(bin_str[9:16] + bin_str[:5])
        # 3 index/second subword
        mixed_words.append(bin_str[29:32] + bin_str[16:24] + bin_str[8:9])

        #------type three |8|4|4|8|------------
        # 4 index/first subword
        mixed_words.append(bin_str[12:16] + bin_str[:8])
        # 5 index/second subword
        mixed_words.append(bin_str[16:24] + bin_str[8:12])

        #------type four |6|2|2|6|8|------------
        # 6 index/first subword
        mixed_words.append(bin_str[10:16] + bin_str[:6])
        # 7 index/second subword
        mixed_words.append(bin_str[30:32] + bin_str[16:24] + bin_str[8:10])

        return mixed_words

    def mix_words(self, bytes_to_mix):
        """ Create 16 bit words from 12 bit words
                         to be recorded in target file """
        middle = self.mix_syncword(bytes_to_mix)
        tmp_str_1 = "0000" + middle[self.mix_type]
        tmp_str_2 = "0000" + middle[self.mix_type + 1]
        mixed_words = [tmp_str_1[8:16], tmp_str_1[0:8],
                       tmp_str_2[8:16], tmp_str_2[0:8]]
        return mixed_words
