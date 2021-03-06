from processing import PrepareData
import os


class SAAB(PrepareData):

    """ SAAB - 340. Creation of parametric
        file with data being processed """

    def __init__(self,  tmp_file_name, param_file_name,
                 progress_bar, path_to_save, flag, tmp_bin_file=None):
        PrepareData.__init__(self, tmp_file_name, param_file_name,
                             progress_bar, path_to_save, flag)
        self.progress_bar.Show()
        self.progress_bar.SetValue(5)
        # make export of parametric info to tmp param file
        if tmp_bin_file:
            self.export_param_saab(tmp_file_name, tmp_bin_file)
            # just created tmp parametric file
            self.source_file = (open(tmp_bin_file, "rb")).read()
        else:
            self.source_file = (open(tmp_file_name, "rb")).read()
        # size of tmp parametric file
        self.param_file_end = len(self.source_file)
        self.progress_bar.SetValue(15)
        #---------- rewrite header to target parametric file
        self.header_to_param_file()
        self.progress_bar.SetValue(35)
        #--------- find mix type scheme
        self.scheme_search()
        self.progress_bar.SetValue(45)
        self.record_data()
        self.progress_bar.SetValue(100)

    def export_param_saab(self, tmp_file_name, tmp_bin_name):

        """ Extract only parametric data into tmp bin file """

        data = open(tmp_file_name, "rb")
        source = data.read()  # flight
        # tmp file with parametric data
        tmp_param_file = open(tmp_bin_name, "wb")
        # rewrite header to tmp parametric file
        tmp_param_file.write(source[:128])
        i = 128  # start after header
        #-------each byte after FF is a parametric byte----
        #-------so we need to write only it--------------
        while i < len(source) - 1:
            if ord(source[i]) == 255:
                tmp_param_file.write(source[i + 1])
                i += 2  # not to read byte that has been already read
            else:
                i += 1
        data.close()
        tmp_param_file.close()