from processing import PrepareData


class SAAB(PrepareData):

    def __init__(self, tmp_file_name, param_file_name, tmp_param_file, frame, subframe):
        PrepareData.__init__(self, tmp_param_file=tmp_param_file, param_file_name=param_file_name,
                             frame_len=frame, subframe_len=subframe)
        self.param_file = open(param_file_name, "wb")  # target parametric file ".inf"
        #----------- make export of parametric info to tmp param file -----------------
        self.export_param_saab(tmp_file_name, tmp_param_file)
        self.source_file = (open(tmp_param_file, "rb")).read()  # just created tmp parametric file
        self.param_file_end = len(self.source_file)  # size of tmp parametric file
        #---------- rewrite header to target parametric file --------------------------
        self.header_to_param_file()
        #--------- find mix type scheme -----------------------------------------------
        self.scheme_search()
        self.record_data()

    def export_param_saab(self, tmp_file_name, tmp_param_file_name):
        """ Extract only parametric data into tmp file """
        data = (open(tmp_file_name, "rb")).read()  # flight
        tmp_param_file = open(tmp_param_file_name, "wb")  # tmp file with parametric data
        tmp_param_file.write(data[:128])  # rewrite header to tmp parametric file
        i = 128  # start after header
        #-------each byte after FF is a parametric byte----
        #-------so we need to write only it--------------
        while i < len(data) - 1:
            if ord(data[i]) == 255:
                tmp_param_file.write(data[i + 1])
                i += 2  # not to read byte that has been already read
            else:
                i += 1
        tmp_param_file.close()