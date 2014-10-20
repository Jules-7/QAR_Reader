from processing import PrepareData
import os

""" A320. Creation of parametric file with data being processed """


class A320(PrepareData):

    def __init__(self, tmp_file_name, param_file_name, frame, subframe, progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name=tmp_file_name, param_file_name=param_file_name,
                             frame_len=frame, subframe_len=subframe, progress_bar=progress_bar,
                             path_to_save=path_to_save, flag=flag)
        source = open(tmp_file_name, "rb")
        self.source_file = source.read()  # just created tmp parametric file
        self.param_file_end = len(self.source_file)  # size of tmp parametric file
        #---------- rewrite header to target parametric file --------------------------
        self.header_to_param_file()
        #--------- find mix type scheme -----------------------------------------------
        self.scheme_search()
        self.record_data()
        source.close()
        #os.remove(tmp_file_name)