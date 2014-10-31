from processing import PrepareData
import os

""" A320. Creation of parametric file with data being processed """


class A320(PrepareData):

    def __init__(self, tmp_file_name, param_file_name, frame, subframe, progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name=tmp_file_name, param_file_name=param_file_name,
                             frame_len=frame, subframe_len=subframe, progress_bar=progress_bar,
                             path_to_save=path_to_save, flag=flag)
        self.progress_bar.Show()
        self.qar_type = flag  # "airbus"
        self.progress_bar.SetValue(5)
        source = open(tmp_file_name, "rb")
        self.source_file = source.read()  # just created tmp parametric file
        self.param_file_end = len(self.source_file)  # size of tmp parametric file
        self.progress_bar.SetValue(15)
        #---------- rewrite header to target parametric file --------------------------
        self.header_to_param_file()
        self.progress_bar.SetValue(25)
        #--------- find mix type scheme -----------------------------------------------
        self.scheme_search()
        self.progress_bar.SetValue(45)
        self.record_data()
        self.progress_bar.SetValue(85)
        source.close()
        self.progress_bar.SetValue(95)
        #os.remove(tmp_file_name)