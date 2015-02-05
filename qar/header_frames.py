#-*-coding: utf-8-*-
import os


class HeaderFrameSearchWrite(object):

    """ record monstr header as it is;
        search for frames and write them.
        same algorithm for MSRP-12 and TesterU3-2
        but with different syncwords"""

    def __init__(self, tmp_file_name, target_file_name, progress_bar,
                 path_to_save, flag, syncword, shift_after_header):
        self.tmp_file_name = tmp_file_name
        self.target_file_name = target_file_name
        self.progress_bar = progress_bar
        self.path_to_save = path_to_save
        self.flag = flag
        self.file_end = False
        self.frame_size = 512  # bytes
        self.syncword_one = syncword
        self.end_pattern = [255] * self.frame_size
        #self.sw_byte_amount = sw_bytes
        #self.syncword_one = ["255", "127"]  # FF7F TesterU3-2
        #self.syncword_one = ["255"]  # FF MSRP12
        #self.syncword_two = ["255", "126"]  # FF7E
        self.source_position = 0

        self.progress_bar.Show()

        self.source = open(self.tmp_file_name, "rb")
        name = (r"%s" % self.path_to_save + r"\\" + r"%s" % self.target_file_name)
        self.target_file = open(name, "wb")

        self.progress_bar.SetValue(5)

        self.bytes_counter = 0
        self.source_len = os.stat(self.tmp_file_name).st_size
        self.record_header()
        #print("recorded header")
        self.progress_bar.SetValue(15)
        if shift_after_header:
            self.source.seek(shift_after_header, 0)
        self.progress_bar.SetValue(25)

        self.record_data()
        #print("recorded data")
        self.progress_bar.SetValue(85)

        self.source.close()
        self.target_file.close()

        self.progress_bar.SetValue(100)

    def record_header(self):
        header = self.source.read(128)
        self.bytes_counter += 128
        self.target_file.write(header)

    def record_data(self):
        """ Record only valid frames """
        while not self.file_end and self.bytes_counter < self.source_len:
            self.source_position = self.source.tell()
            sw = self.find_syncword()
            while sw:
                checked = self.check_frame()
                if checked:
                    frame = self.source.read(self.frame_size)
                    self.target_file.write(frame)
                    self.bytes_counter += self.frame_size
                    self.source_position = self.source.tell()
                    # -2 as we already know that first two bytes are syncword
                    #self.source.seek(-(self.frame_size - 2), 1)
                else:
                    # need to include those bytes which have been read,
                    # but not included
                    # as there was no syncword -> equate to position in source file
                    self.source.seek(-self.frame_size, 1)
                    self.source_position = self.source.tell()
                    check = self.check_for_not_end_pattern()
                    self.source_position = self.source.tell()
                    if check:
                        position_at_source = self.source.tell()
                        self.bytes_counter = position_at_source
                    break

    def find_syncword(self):
        """ byte by byte search for syncword
           if within one frame size it was not found -> check for data end """
        byte_amount = len(self.syncword_one)  # 2 or 1
        # count total amount of bytes, which have been checked for syncword
        checked_bytes = 0
        self.source_position = self.source.tell()
        while not self.file_end and self.bytes_counter < self.source_len:
            syncword = []
            for each in self.syncword_one:
                byte_one = self.source.read(1)
                checked_bytes += 1
                try:
                    syncword.append(str(ord(byte_one)))
                except TypeError:  # end of file
                    self.file_end = True
                    break
            if syncword == self.syncword_one:
                self.source.seek(-byte_amount, 1)
                return True
            else:
                # in case of 2 byte syncword we need to go back one byte
                # in case of 1 byte syncword we don`t need to go back
                # correspondingly in case of 2 byte sw - we increase bytes_counter
                # in case of 1 byte sw we don`t increase bytes_counter
                #print(self.source.tell())
                #print(self.source_len)
                self.source.seek(-(byte_amount - 1), 1)
                self.bytes_counter += (byte_amount - 1)
                checked_bytes -= 1
                self.source_position = self.source.tell()
            if checked_bytes >= self.frame_size:
                self.source_position = self.source.tell()
                # if within frame size syncword was not found -> check for data end
                check = self.check_for_not_end_pattern()
                self.source_position = self.source.tell()
                if not check:  # end pattern was found
                    break
                else:  # end pattern was not found
                    checked_bytes = 0

    def check_frame(self):
        """ check syncword """
        byte_amount = len(self.syncword_one)  # 2 or 1
        syncword = []
        self.source.seek(self.frame_size, 1)

        for each in self.syncword_one:
            byte_one = self.source.read(1)
            if byte_one == "":
                self.file_end = True
                return
            else:
                syncword.append(str(ord(byte_one)))
        self.source_position = self.source.tell()
        if syncword == self.syncword_one:
            self.source.seek(-(self.frame_size + byte_amount), 1)
            #self.source_position = self.source.tell()
            return True
        return False

    def check_for_not_end_pattern(self):
        # as an end pattern (one frame of FF) is not necessarily within one frame
        # starting from the index we check,
        # we should check two frames, so this pattern will definitely be inside
        self.source_position = self.source.tell()
        frame = self.source.read(self.frame_size * 2)
        self.source_position = self.source.tell()
        counter = 0
        for each in frame:
            if ord(each) == 255:
                counter += 1
            else:
                counter = 0
            if counter == self.frame_size:
                self.source.seek(-self.frame_size, 1)
                self.file_end = True
                return False
        self.source.seek(-(self.frame_size * 2), 1)
        self.source_position = self.source.tell()
        return True