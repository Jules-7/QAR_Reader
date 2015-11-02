import struct

apply_swap = lambda x: (x * 0x0202020202 & 0x010884422010) % 1023


class ReverseByte(object):

    def __init__(self, path, progress_bar, path_to_save):
        self.path = path
        self.progress_bar = progress_bar
        self.path_to_save = path_to_save
        self.open_file()

    def open_file(self):
        data = open(self.path, 'rb')
        target_file = open(self.path_to_save, "wb")
        while True:
            bytes_array = data.read(512)
            if bytes_array == "":
                break
            for each in bytes_array:
                dat = ord(each)
                swaped = self.swap_byte(dat)
                value = int(swaped, 2)
                to_write = (struct.pack("i", value))[:1]
                target_file.write(to_write)

    def swap_byte(self, byte):
        #print '{} -> {}'.format(bin(i)[2:].zfill(8), bin(apply_swap(i))[2:].zfill(8))
        return bin(apply_swap(byte))[2:].zfill(8)
