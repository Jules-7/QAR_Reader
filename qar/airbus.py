from processing import PrepareData

""" A320. Creation of parametric file with data being processed """


class A320(PrepareData):

    def __init__(self, param_file_name, tmp_param_file, frame, subframe, progress_bar, path_to_save):
        PrepareData.__init__(self, tmp_param_file=tmp_param_file, param_file_name=param_file_name,
                             frame_len=frame, subframe_len=subframe, progress_bar=progress_bar,
                             path_to_save=path_to_save)
        print(self.param_file)
        self.source_file = (open(tmp_param_file, "rb")).read()  # just created tmp parametric file
        self.param_file_end = len(self.source_file)  # size of tmp parametric file
        #---------- rewrite header to target parametric file --------------------------
        #self.header_to_param_file()
        #--------- find mix type scheme -----------------------------------------------
        self.scheme_search()
        self.record_data()