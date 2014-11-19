#-*-coding: utf-8-*-
import os


class HeaderFrameSearchWrite(object):

    """ record monstr header as it is;
        search for frames and write them
        same algorithm for MSRP-12 and TesterU3-2 but with different syncwords"""

    def __init__(self, tmp_file_name, target_file_name, progress_bar, path_to_save, flag,
                 syncword, shift_after_header):
        self.tmp_file_name = tmp_file_name
        self.target_file_name = target_file_name
        self.progress_bar = progress_bar
        self.path_to_save = path_to_save
        self.flag = flag
        self.file_end = False
        self.frame_size = 512  # bytes
        self.syncword_one = syncword
        #self.sw_byte_amount = sw_bytes
        #self.syncword_one = ["255", "127"]  # FF7F TesterU3-2
        #self.syncword_one = ["255"]  # FF MSRP12
        #self.syncword_two = ["255", "126"]  # FF7E

        self.source = open(self.tmp_file_name, "rb")
        name = (r"%s" % self.path_to_save + r"\\" + r"%s" % self.target_file_name)
        self.target_file = open(name, "wb")
        self.bytes_counter = 0
        self.source_len = os.stat(self.tmp_file_name).st_size
        self.record_header()
        #self.source.seek(384, 0) shift after header for MSRP-12
        if shift_after_header:
            self.source.seek(shift_after_header, 0)
        self.record_data()
        self.source.close()
        self.target_file.close()

    def record_header(self):
        header = self.source.read(128)
        self.bytes_counter += 128
        self.target_file.write(header)

    def record_data(self):
        while self.bytes_counter < self.source_len - self.frame_size:
            if self.file_end:
                break
            sw = self.find_syncword()
            while sw:
                #p1 = self.source.tell()
                checked = self.check_frame()
                if checked:
                    #pp1 = self.source.tell()
                    frame = self.source.read(self.frame_size)
                    #pp2 = self.source.tell()
                    self.target_file.write(frame)
                    self.bytes_counter += self.frame_size
                    # -2 as we already know that first two bytes are syncword
                    #self.source.seek(-(self.frame_size - 2), 1)
                    #pp3 = self.source.tell()
                else:
                    # need to include those bytes which have been read, but not included
                    # as there was no syncword -> equate to position in source file
                    position_at_source = self.source.tell()
                    self.bytes_counter = position_at_source
                    break

    def find_syncword(self):
        byte_amount = len(self.syncword_one)  # 2 or 1
        while self.bytes_counter < self.source_len - self.frame_size:
            #p2 = self.source.tell()
            syncword = []
            for each in self.syncword_one:
                byte_one = self.source.read(1)
                #byte_two = self.source.read(1)
                try:
                    syncword.append(str(ord(byte_one)))
                except TypeError:  # end of file
                    self.file_end = True
                    break
            #if syncword == self.syncword_one or syncword == self.syncword_two:
            if syncword == self.syncword_one:
                self.source.seek(-byte_amount, 1)
                #p4 = self.source.tell()
                return True
            else:
                # in case of 2 byte syncword we need to go back one byte
                # in case of 1 byte syncword we don`t need to go back
                # correspondingly in case of 2 byte sw - we increase bytes_counter
                # in case of 1 byte sw we don`t increase bytes_counter
                ppppppp4 = self.source.tell()
                self.source.seek(-(byte_amount - 1), 1)
                ppppppp5 = self.source.tell()
                self.bytes_counter += (byte_amount - 1)
                ppppppp6 = self.source.tell()

    def check_frame(self):
        byte_amount = len(self.syncword_one)  # 2 or 1
        syncword = []
        #p3 = self.source.tell()
        self.source.seek(self.frame_size, 1)
        #pppp4 = self.source.tell()

        for each in self.syncword_one:
            byte_one = self.source.read(1)
            #byte_two = self.source.read(1)
            if byte_one == "":
                self.file_end = True
                return
                # return False
            else:
                syncword.append(str(ord(byte_one)))
        if syncword == self.syncword_one:
            #pp4 = self.source.tell()
            self.source.seek(-(self.frame_size + byte_amount), 1)
            #self.bytes_counter += self.frame_size
            #pp5 = self.source.tell()
            return True
