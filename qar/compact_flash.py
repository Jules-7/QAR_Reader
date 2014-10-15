import os


class CompactFlash(object):

    def __init__(self, path):
        self.header_len = 32  # Bytes
        self.frame_len = 768  # Bytes
        self.cluster_size = 8192
        self.flight_end_sign = [[0] * self.frame_len, [255] * self.frame_len]
        self.frame_duration = 4  # sec
        self.qar_type = None
        self.path = path
        transformed_path = r"\\.\%s" % self.path[:2]
        self.dat = file(transformed_path, "rb")
        self.cf_end_index = 0
        self.flights = []
        self.flight_intervals = []
        self.headers = []
        self.date = []
        self.time = []
        self.header_pattern = []
        self.init_date = None
        self.bytes_counter = 0
        self.flights_starts = []
        self.flights_ends = []
        self.start_index = 0
        self.end_index = 0
        self.curr_date = []
        self.durations = []
        self.end_date = []

        copy_file = self.copy_cf_data()
        self.source = open(copy_file, "rb")
        self.source_len = os.stat(copy_file).st_size

        self.get_header_pattern()

        self.find_flights()
        #self.get_durations()
        #self.get_qar_type()


    def copy_cf_data(self):
        copy_name = "E:/cf.tmp"
        new_file = open(copy_name, "wb")
        counter = 0
        while counter < (500400*512):
            new_file.write(self.dat.read(512))
            counter += 512
        self.dat.close()
        new_file.close()
        return copy_name

    def get_header_pattern(self):
        while not self.header_pattern:
            next_byte = self.source.read(1)
            self.bytes_counter += 1
            if ord(next_byte) != 0:
                self.source.seek(-1, 1)
                self.bytes_counter -= 1
                self.headers.append(self.source.read(self.header_len))
                self.header_pattern.append(ord(self.headers[0][0]))
                self.header_pattern.append(ord(self.headers[0][1]))
                self.start_index = self.bytes_counter
                self.flights_starts.append(self.start_index)
                self.source.seek(-self.header_len, 1)

    def find_flights(self):
        while self.bytes_counter < self.source_len - self.cluster_size - 16:
            self.source.seek(self.cluster_size, 1)
            self.bytes_counter += self.cluster_size
            next_byte = self.source.read(1)
            try:
                if (ord(next_byte) == self.header_pattern[0] and
                    ord(self.source.read(1)) == self.header_pattern[1]):
                    # check previous 48 bytes
                    self.source.seek(-50, 1)
                    prev_48_bytes = self.source.read(48)
                    prev_bytes_list = [ord(each) for each in prev_48_bytes]
                    end_pattern = [0]*48
                    if prev_bytes_list == end_pattern:
                        self.flights_starts.append(self.bytes_counter)
                        self.headers.append(self.source.read(self.header_len))
                        self.source.seek(-self.header_len, 1)
            except TypeError:
                break
        print(self.flights_starts)


'''
    def find_start(self):
        while True:
            next_byte = self.source.read(1)
            self.bytes_counter += 1
            if not next_byte:
                self.cf_end_index = self.bytes_counter
            if ord(next_byte) != 0:
                start_index = self.bytes_counter
                self.source.seek(-1, 1)
                self.flights_starts.append(start_index)
                print("start %s" % start_index)
                break

    def find_end(self):
        self.headers.append(self.source.read(self.header_len))  # read 32 bytes
        self.bytes_counter += self.header_len
        # perform reading by frames

        check_cluster = self.source.read(self.fr)
        self.bytes_counter += self.frame_len
        frame_check = []
        for each in next_frame:
            frame_check.append((hex(ord(each)))[2:])
        while True:
            if frame_check == self.flight_end_sign[0] or frame_check == self.flight_end_sign[1]:
                end_index = self.bytes_counter
                self.flights_ends.append(end_index)
                print("end %s" % end_index)
                break
            del frame_check[0]
            next_byte = self.source.read(1)
            if not next_byte:
                self.cf_end_index = self.bytes_counter
                break
            frame_check.append((hex(ord(next_byte)))[2:])
            self.bytes_counter += 1

    def find_flights(self):
        while not self.cf_end_index:
            self.find_start()
            self.find_end()'''

'''while True:
            next_byte = self.dat.read(1)
            self.bytes_counter += 1
            if ord(next_byte) == 0:
                end_index = self.bytes_counter
                print("end %s" % end_index)
                self.flights_ends.append(end_index)
                break
            else:
                self.dat.read((8192 - 1))'''