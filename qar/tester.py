#-*-coding: utf-8-*-
import os


class TesterU32(object):

    """ Perform frames check -> save only valid frames"""

    def __init__(self, tmp_file_name, target_file_name, progress_bar, path_to_save, flag):
        self.tmp_file_name = tmp_file_name
        self.target_file_name = target_file_name
        self.progress_bar = progress_bar
        self.path_to_save = path_to_save
        self.flag = flag
        self.file_end = False
        self.frame_size = 512  # bytes
        self.syncword_one = ["255", "127"]  # FF7F
        #self.syncword_two = ["255", "126"]  # FF7E
        self.source = open(self.tmp_file_name, "rb")
        name = (r"%s" % self.path_to_save + r"\\" + r"%s" % self.target_file_name)
        print(self.tmp_file_name)
        print(self.target_file_name)
        print(self.path_to_save)
        print(self.flag)
        print(self.source)
        print(name)
        self.target_file = open(name, "wb")
        self.bytes_counter = 0
        self.source_len = os.stat(self.tmp_file_name).st_size
        self.record_header()
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
                p1 = self.source.tell()
                checked = self.check_frame()
                if checked:
                    frame = self.source.read(self.frame_size)
                    self.target_file.write(frame)
                    # -2 as we already know that first two bytes are syncword
                    self.source.seek(-(self.frame_size - 2), 1)
                else:
                    break

    def find_syncword(self):
        while self.bytes_counter < self.source_len - self.frame_size:
            p2 = self.source.tell()
            byte_one = self.source.read(1)
            byte_two = self.source.read(1)
            try:
                syncword = [str(ord(byte_one)), str(ord(byte_two))]
            except TypeError:  # end of file
                self.file_end = True
                break
            #if syncword == self.syncword_one or syncword == self.syncword_two:
            if syncword == self.syncword_one:
                return True
            else:
                self.source.seek(-1, 1)
                self.bytes_counter += 1

    def check_frame(self):
        p3 = self.source.tell()
        self.source.seek(self.frame_size - 2, 1)
        p4 = self.source.tell()
        byte_one = self.source.read(1)
        byte_two = self.source.read(1)
        syncword = [str(ord(byte_one)), str(ord(byte_two))]
        #if syncword == self.syncword_one or syncword == self.syncword_two:
        if syncword == self.syncword_one:
            self.source.seek(-2, 1)
            self.bytes_counter += self.frame_size
            return True


