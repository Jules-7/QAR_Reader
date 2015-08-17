from processing import PrepareData


class A320(PrepareData):

    """ A320. Creation of parametric file with data being processed """

    def __init__(self, tmp_file_name, param_file_name,
                 progress_bar, path_to_save, flag):
        PrepareData.__init__(self, tmp_file_name, param_file_name,
                             progress_bar, path_to_save, flag)
        self.progress_bar.Show()
        self.progress_bar.SetValue(5)

        source = open(tmp_file_name, "rb")
        # open just created tmp parametric file
        self.source_file = source.read()

        # size of tmp parametric file
        self.param_file_end = len(self.source_file)
        self.progress_bar.SetValue(15)

        # rewrite header to target parametric file
        self.header_to_param_file()
        self.progress_bar.SetValue(25)

        # find mix type scheme
        self.scheme_search()
        self.progress_bar.SetValue(45)

        self.record_data()
        self.progress_bar.SetValue(85)

        source.close()
        self.progress_bar.SetValue(100)