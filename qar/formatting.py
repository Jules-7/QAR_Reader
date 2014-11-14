#-*-coding: utf-8-*-
import os
import struct
import stat


class FormatCompactFlash(object):

    def __init__(self, path):
        self.path = path
        self.card_size = 4 * 1024 * 1024 * 1024  # bytes
        self.format_compact_flash()

    def format_compact_flash(self):
        """ Formatting clears file -> fill whole file with zeros
        This process takes about 40 min """
        byte_counter = 0
        #os.chmod(r"%s" % self.path[:3], stat.S_IWRITE)  # change mode for writing
        correct_path = r"\\.\%s" % str(self.path)[:2]

        dat_3 = file(correct_path, "rb+")
        zeros = (struct.pack("i", 0))
        while byte_counter <= self.card_size:
            dat_3.write(zeros)
            byte_counter += 4
        #dat_3.close()
