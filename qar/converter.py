import struct
import os


class Converter(object):
    """ Convert n bit wird to 16 bit word by adding zeroes """
    def __init__(self, path, path_to_save, progress_bar):
        self.path = path
        self.path_to_save = path_to_save
        self.progress_bar = progress_bar
        self.source = open(self.path, "rb")
        self.frame_size = None
        self.bytes_counter = 0
        self.source_size = os.stat(self.path).st_size
        self.word_size = None  # initial 12 bit word

    def form_new_name(self):
        slash = self.path.rfind("\\")
        dot = self.path.rfind('.')
        name_of_file = self.path[slash:dot]
        self.target_file = open(r"%s" % self.path_to_save + str(name_of_file) + "_16B" + ".inf", "wb")

    def get_frame(self):
        while self.bytes_counter < self.source_size:
            frame = self.source.read(self.frame_size)
            self.bytes_counter += self.frame_size
            data = ""
            for each in frame:
                data += (str(bin(ord(each)))[2:]).rjust(8, "0")
            self.record_data(data)

    def write_to_file(self, bytes_to_write):
        for each in bytes_to_write:
            str_to_int = int(each, 2)
            data_to_write = struct.pack("i", str_to_int)
            self.target_file.write(data_to_write[:1])

    def record_data(self, data):
        i = 0
        while i <= len(data) - self.word_size:
            # get 10 bit word
            word = data[i:i+self.word_size]
            # insert zeroes
            if self.order == "direct":
                bytes_to_write = ["000000" + word[:2], word[2:]]
            elif self.order == "reverse":
                bytes_to_write = [word[0:8], "0000" + word[8:]]
            self.write_to_file(bytes_to_write)
            i += self.word_size
        return


class TwelveToSixteen(Converter):

    """ Convert twelve bit words to sixteen bit words by adding zeroes
         after the first byte -> first 8 bits record as it is, add 4 zeroes +
         remaining part of 12 bit word """

    def __init__(self, path, path_to_save, progress_bar):
        Converter.__init__(self, path, path_to_save, progress_bar)
        self.frame_size = 576  # B
        self.word_size = 12  # initial 12 bit word
        self.order = "reverse"  # need to switch bytes

        self.progress_bar.Show()
        self.progress_bar.SetValue(15)
        self.form_new_name()

        self.progress_bar.SetValue(35)

        self.get_frame()

        self.progress_bar.SetValue(100)


class TenToSixteen(Converter):

    """ Convert ten bit words to sixteen bit words by adding zeroes
         0000 + 10 bit word
    """

    def __init__(self, path, path_to_save, progress_bar):
        Converter.__init__(self, path, path_to_save, progress_bar)
        self.frame_size = 600  # B
        self.word_size = 10  # initial 12 bit word
        self.order = "direct"  # add zeroes at the beginning of the word

        self.progress_bar.Show()
        self.progress_bar.SetValue(15)
        self.form_new_name()

        self.progress_bar.SetValue(35)

        self.get_frame()

        self.progress_bar.SetValue(100)
