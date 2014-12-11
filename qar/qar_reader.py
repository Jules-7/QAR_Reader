#-*-coding: utf-8-*-
from threading import *
import wx
import re
import time
from extractFlight import Flight
from splitter import Split
from datetime import datetime
from initialization import Initialize
import wx.lib.filebrowsebutton as filebrowse
from formatting import FormatCompactFlash
"""this module:
- creates window for choosing of file with flights
- displays all flights in file
- allows to save flight as raw data or as flight according
to QAR type"""

ACCESS = {1: ["admin", "admin", (700, 500)],
          10: ["yanair", " ", (600, 500)],
          11: ["gap_ukraine", u'ГАП "Украина" Ан148 БУР-92 А-05', (600, 500)],
          12: ["VCH", u'В/Ч №2269', (600, 500)]}

# admin
USER = 12

# YanAir
#USER = 10

# title for window depending on USER
WIN_TITLE = ACCESS[USER][1]

# size of main window
SIZE = ACCESS[USER][2]

# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()
# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()


def event_result(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class WorkerThread(Thread):  # Thread class that executes processing
    """Worker Thread Class."""
    def __init__(self, notify_window, path, flag):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.path = path
        self.flag = flag
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread
        s = Split(self.path, self.flag)
        q = s.result
        # Here's where the result would be returned
        wx.PostEvent(self._notify_window, ResultEvent(q))
        return


########################################################################
class MyPanel(wx.Panel):
    """ Panel to display flights in main window """
    #----------------------------------------------------------------------
    def __init__(self, parent, data, path):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.path = path
        self.qar_type = data.qar_type
        self.selected_flight = []
        self.selected_parent_set = []

        # list of items with scroll
        self.list_ctrl = wx.ListCtrl(self,
                                     style=wx.LC_REPORT
                                     | wx.BORDER_SUNKEN,
                                     size=(2000, 2000))
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.list_ctrl.InsertColumn(0, u"Flight №", width=70)
        self.list_ctrl.InsertColumn(1, "ID", width=100)
        self.list_ctrl.InsertColumn(2, "Start date", width=140)
        self.list_ctrl.InsertColumn(3, "End date", width=140)
        self.list_ctrl.InsertColumn(4, "Duration", width=100)

        index = 0
        self.flights_dict = {}
        # in case there are no flights in file
        if not data.flight_intervals:
            self.no_flights = True
        else:
            self.no_flights = False
        for each in data.flight_intervals:
            try:
                flight = str(data.flight_intervals[index][0]) + ":" + str(data.flight_intervals[index][1])
            except IndexError:
                flight = str(data.flight_intervals[index][0]) + ":" + str(0)

            start_date = "%s %s" % (data.start_date[index].strftime('%d.%m.%Y'),
                                    data.start_date[index].time())
            end_date = "%s %s" % (data.end_date[index].strftime('%d.%m.%Y'),
                                  data.end_date[index].time())
            seconds = data.durations[index]
            m, sec = divmod(seconds, 60)
            hours, minutes = divmod(m, 60)
            duration = "%02d h %02d m %02d s" % (hours, minutes, sec)
            #duration = time.strftime('%d h %02d m %02 s',% (h, m, s)
                                     #time.gmtime())
            #InsertStringItem provides creation of next string
            #without it impossible to create list
            self.list_ctrl.InsertStringItem(index, str(index + 1))
            self.list_ctrl.SetStringItem(index, 1, str(data.flights_start[index]))
            self.list_ctrl.SetStringItem(index, 2, start_date)
            self.list_ctrl.SetStringItem(index, 3, end_date)
            self.list_ctrl.SetStringItem(index, 4, duration)

            #associate index of row with particular flight
            self.flights_dict[index] = [flight, index, start_date, self.qar_type]
            index += 1

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    #----------------------------------------------------------------------
    def on_item_selected(self, event):
        """ at row selection - index is returned
        using that index search for flight from flights_dict
        and pass it for processing """
        self.selected_parent_set = []
        self.parent.selected = []
        #-------- Ensures multiple flights selection -----------
        flight_number = self.list_ctrl.GetFirstSelected()
        self.selected_flight = [flight_number]
        while True:
            # check for another flight been chosen
            # in GetNextSelected(flight_number) -> flight number
            # is given in order to look after this number
            item = self.list_ctrl.GetNextSelected(flight_number)
            if item == -1:  # nor next choice
                break
            else:
                flight_number = item
                self.selected_flight.append(flight_number)
        #print(self.selected_flight)
        for each in self.selected_flight:
            self.selected_parent_set.append(self.flights_dict[each])
        #chosen_flights = [each[0] for each in self.selected_parent_set]
        #print(chosen_flights)
        #print(self.selected_parent_set)
        for choice in self.selected_parent_set:
            self.parent.selected.append(choice)
        #print(self.parent.selected)
        self.parent.progress_bar.Hide()


class InitializationFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Initialization settings", size=(400, 350))
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = InitializationPanel(self)
        self.sizer.Add(panel)
        self.sizer.Layout()


class InitializationPanel(wx.Panel):

    """ Panel to display Initialization settings menu """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.drive = None
        self.qar_type = None
        self.date = datetime.today()
        self.time = datetime.now().strftime('%H:%M:%S')
        self.flight_n = None
        self.qar_n = None

        title = wx.StaticText(self, -1,
                              "Please choose options for initialization")
        path_to_drive = filebrowse.DirBrowseButton(self, -1, size=(350, -1),
                                                   changeCallback = self.get_drive,
                                                   labelText="Choose a drive")
        qar_type_list = ['A320 - QAR',
                         'A320 - Compact Flash',
                         'B747 - QAR',
                         'An148 - BUR-92',
                         'SAAB',
                         'QAR-2100',
                         'QAR-4100',
                         'QAR-4120',
                         'QAR-4700']
        select_txt = wx.StaticText(self, -1, "Select qar type", (2, 50))
        choose_qar_type = wx.Choice(self, -1, size=(100, -1), choices=qar_type_list)

        date_txt = wx.StaticText(self, -1, "Select date", (2, 50))
        pick_date = wx.GenericDatePickerCtrl(self, size=(120, -1),
                                             style = wx.DP_DROPDOWN
                                             | wx.DP_SHOWCENTURY
                                             | wx.DP_ALLOWNONE)
        time_now = datetime.now().strftime('%H:%M:%S')
        time_txt = wx.StaticText(self, -1, " and time ", (2, 50))
        time_input = wx.TextCtrl(self, -1, size=(140, -1))
        time_input.SetValue('%s' % time_now)
        flight_N_txt = wx.StaticText(self, -1, "Insert flight number", (2, 50))
        self.flight_N = wx.TextCtrl(self, -1, size=(140, -1))
        qar_N_txt = wx.StaticText(self, -1, "Insert QAR number", (2, 50))
        self.qar_N = wx.TextCtrl(self, -1, size=(140, -1))
        ok_button = wx.Button(self, id=1111, label="Ok")
        cancel_button = wx.Button(self, id=2222, label="Cancel")

        general_sizer = wx.BoxSizer(wx.VERTICAL)
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        qar_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        flight_N_sizer = wx.BoxSizer(wx.HORIZONTAL)
        qar_N_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        #element to add, proportion, apply border to side, width of border
        title_sizer.Add(title, 0, wx.ALL, 5)

        path_sizer.Add(path_to_drive, 0, wx.ALL, 5)

        qar_type_sizer.Add(select_txt, 0, wx.ALL, 5)
        qar_type_sizer.Add(choose_qar_type, 1, wx.ALL, 5)

        date_sizer.Add(date_txt, 0, wx.ALL, 5)
        date_sizer.Add(pick_date, 1, wx.ALL, 5)
        date_sizer.Add(time_txt, 2, wx.ALL, 5)
        date_sizer.Add(time_input, 3, wx.ALL, 5)

        flight_N_sizer.Add(flight_N_txt, 0, wx.ALL, 5)
        flight_N_sizer.Add(self.flight_N, 1, wx.ALL | wx.EXPAND, 5)

        qar_N_sizer.Add(qar_N_txt, 0, wx.ALL, 5)
        qar_N_sizer.Add(self.qar_N, 0, wx.ALL, 5)

        buttons_sizer.Add(ok_button, 0, wx.ALL, 5)
        buttons_sizer.Add(cancel_button, 0, wx.ALL, 5)

        general_sizer.Add(title_sizer, 0, wx.CENTER)
        general_sizer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(path_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(qar_type_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(date_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(flight_N_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(qar_N_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(buttons_sizer, 0, wx.ALL | wx.CENTER, 5)

        self.SetSizer(general_sizer)

        self.Bind(wx.EVT_CHOICE, self.qar_type_choice, choose_qar_type)
        self.Bind(wx.EVT_DATE_CHANGED, self.on_date_changed, pick_date)
        self.Bind(wx.EVT_TEXT, self.on_time_changed, time_txt)
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)
        self.Bind(wx.EVT_CLOSE, self.on_cancel)

    def get_drive(self, event):
        self.drive = event.GetString()

    def qar_type_choice(self, event):
        self.qar_type = event.GetString()

    def on_date_changed(self, event):
        self.date = event.GetDate()

    def on_time_changed(self, event):
        self.time = event.GetString()

    def on_ok(self, event):
        try:
            flight_n = self.flight_N.GetValue()
            self.flight_n = flight_n
        except AttributeError:
            self.flight_n = None
        try:
            qar_n = self.qar_N.GetValue()
            self.qar_n = qar_n
        except AttributeError:
            self.qar_n = None
        if not self.drive or not self.qar_type:
            warn_message = wx.MessageDialog(self,
                                            message="Choose both drive and Initialization type",
                                            caption="Warning",
                                            style=wx.OK | wx.CENTRE,
                                            pos=wx.DefaultPosition)
            warn_message.ShowModal()
        else:
            wait = wx.BusyInfo("Please wait, working...")
            i = Initialize(self.drive, self.qar_type, self.date,
                           self.time, self.flight_n, self.qar_n)
            del wait
            done_message = wx.MessageDialog(self, message="Initialization is over",
                                            caption="Fulfilment message",
                                            style=wx.OK | wx.CENTRE,
                                            pos=wx.DefaultPosition)
            done_message.ShowModal()
            self.parent.Close()

    def on_cancel(self, event):
        self.parent.Close()

########################################################################

QAR_TYPES = {0: "msrp12",  # An26
             14: "testerU32",  # An32, An72
             70: "Compact Flash",  # A320
             71: "QAR-B747",
             72: "bur92",  # An148
             73: "QAR-2100",
             74: "QAR-4100",
             75: "QAR-4120",
             76: "QAR-4700",
             254: "QAR SAAB",  # S340
             255: "QAR-R"}


class MyFrame(wx.Frame):

    """"""



    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "QAR Reader  %s" % WIN_TITLE, size=SIZE)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.create_status_bar()
        self.chosen_acft_type = None  # means both acft type and data source type
        self.acft_data_types = {321: ["a320", "qar"],  # A320
                                322: ["a320", "cf"],
                                331: ["b747", "qar"],
                                341: ["an148", "bur92"],
                                351: ["an32", "testerU32"],
                                361: ["an26", "msrp12"],
                                371: ["an72", "testerU32"],
                                381: ["an74", "bur3"],
                                391: ["s340", "qar"],
                                401: ["b737", "qar"],
                                402: ["b737", "fdr"],
                                403: ["b737", "4700"]}

        self.selected = []  # flights selected from list
        self.create_file_menu()
        self.create_tool_bar()
        self.saved_flights = []  # flights which are already processed and saved
        self.init_options = []

        self.Show()
        event_result(self, self.on_open_file)
        self.SetSizer(self.sizer)
        #print(self.__module__)
        #print(self.__dict__)
        #print(self.__bases__)

    def create_status_bar(self):
        # Create StatusBar in the bottom of the window
        self.statusbar = self.CreateStatusBar()
        # Set number of fields in statusbar
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-2, -1, 200])

        self.progress_bar = wx.Gauge(self.statusbar, -1,
                                     style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(2)
        self.progress_bar.SetPosition((rect.x + 2, rect.y + 2))
        self.progress_bar.SetSize((rect.width - 4, rect.height - 4))
        self.progress_bar.Hide()

    def create_file_menu(self):
        """ Each user access is defined by access (ability to see)
            aircraft type buttons/file menu options
            Check of user ensures display of this user options
            Access (visibility) of each option
            in file_menu and tool_bar is the same """
        filemenu = wx.Menu()
        #choose_file = filemenu.Append(301, "&Choose", " Choose file to open")

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            initialize = filemenu.Append(wx.ID_ANY, "&Initialize", " Initialize QAR")
            choose_cf = filemenu.Append(302, "&Choose Compact Flash", " Choose Compact Flash to open")
            formatting = filemenu.Append(wx.ID_ANY, "&Format CF", " Formatting Compact Flash")
        menu_exit = filemenu.Append(wx.ID_EXIT, "&Exit", " Terminate the program")
        filemenu.AppendSeparator()

        savemenu = wx.Menu()
        save_file = savemenu.Append(311, "&Save", " Safe flight")
        #save_raw_file = savemenu.Append(312, "&Save RAW", " Save raw data")
        savemenu.AppendSeparator()

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            a320menu = wx.Menu()
            a320_qar = a320menu.Append(321, "&QAR", "Process data from QAR")
            a320_cf = a320menu.Append(322, "&Compact Flash", " Process data from compact flash")
            a320menu.AppendSeparator()

        if ACCESS[USER][0] == "admin":
            b747menu = wx.Menu()
            b747_qar = b747menu.Append(331, "&QAR", "Process data from QAR")
            b747menu.AppendSeparator()

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "gap_ukraine":
            an148menu = wx.Menu()
            an148_qar = an148menu.Append(341, "&QAR", "Process data from QAR")

        if ACCESS[USER][0] == "admin":
            an32menu = wx.Menu()
            an32_qar = an32menu.Append(351, "&QAR", "Process data from QAR")

        if ACCESS[USER][0] == "admin":
            an26menu = wx.Menu()
            an26_qar = an26menu.Append(361, "&QAR", "Process data from QAR")

        if ACCESS[USER][0] == "admin":
            an72menu = wx.Menu()
            an72_qar = an72menu.Append(371, "&QAR", "Process data from QAR")

        if ACCESS[USER][0] == "admin":
            an74menu = wx.Menu()
            an74_qar = an74menu.Append(381, "&QAR", "Process data from QAR")

        menubar = wx.MenuBar()  # Creating the menubar
        menubar.Append(filemenu, "&File")  # Adding the "filemenu" to the MenuBar
        menubar.Append(savemenu, "&Save")  # Adding the "savemenu" to the MenuBar

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            menubar.Append(a320menu, "&A320")

        if ACCESS[USER][0] == "admin":
            menubar.Append(b747menu, "&B747")

        if ACCESS[USER][0] == "admin":
            menubar.Append(an26menu, "&AN26")

        if ACCESS[USER][0] == "admin":
            menubar.Append(an32menu, "&AN32")

        if ACCESS[USER][0] == "admin":
            menubar.Append(an72menu, "&AN72")

        if ACCESS[USER][0] == "admin":
            menubar.Append(an74menu, "&AN74")

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "gap_ukraine":
            menubar.Append(an148menu, "&AN148")

        self.SetMenuBar(menubar)  # Adding the MenuBar to the Frame content.

        #--------- Bindings of buttons/commands with methods
        self.Bind(wx.EVT_TOOL, self.on_choose_file, id=133)
        #self.Bind(wx.EVT_MENU, self.on_choose_file, choose_file)


        self.Bind(wx.EVT_TOOL, self.save_flight, id=134)  # bind with toolbar
        self.Bind(wx.EVT_MENU, self.save_flight, save_file)  # bind with filemenu
        #self.Bind(wx.EVT_TOOL, self.save_raw, id=135)
        #self.Bind(wx.EVT_MENU, self.save_raw, save_raw_file)
        self.Bind(wx.EVT_MENU, self.on_close, menu_exit)

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            self.Bind(wx.EVT_MENU, self.initialization, initialize)
            self.Bind(wx.EVT_MENU, self.formatting, formatting)
            self.Bind(wx.EVT_MENU, self.on_choose_cf, choose_cf)
            self.Bind(wx.EVT_MENU, self.a320_qar_chosen, a320_qar)
            self.Bind(wx.EVT_TOOL, self.a320_cf_chosen, a320_cf)
        # filemenu

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.b747_qar_chosen, b747_qar)

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.an148_qar_chosen, an148_qar)

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.an32_qar_chosen, an32_qar)

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.an26_qar_chosen, an26_qar)

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.an72_qar_chosen, an72_qar)

        if ACCESS[USER][0] == "admin":
            self.Bind(wx.EVT_TOOL, self.an74_qar_chosen, an74_qar)

    def create_tool_bar(self):
        """ Each user access is defined by access (ability to see)
            aircraft type buttons/file menu options
            Check of user ensures display of this user options
            Access (visibility) of each option
            in file_menu and tool_bar is the same """
        # do not use this at window reload -> toolbar is not a=show at first and
        # then it appears on top of flights data
        #self.toolbar = wx.ToolBar(self, -1)
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((30, 30))
        #at executable creation -> place images to the same folder and change path
        #self.toolbar.AddLabelTool(133, 'Open', wx.Bitmap('E:/open_folder.png'))
        self.toolbar.AddLabelTool(134, 'Save', wx.Bitmap('E:/save.png'))
        #self.toolbar.AddLabelTool(135, 'Save RAW', wx.Bitmap('E:/save_raw.png'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            self.toolbar.AddLabelTool(136, 'Open CF', wx.Bitmap('E:/open_CF.png'))
            self.toolbar.AddLabelTool(140, "A320", wx.Bitmap('E:/a320.bmp'))

        if ACCESS[USER][0] == "admin":
            self.toolbar.AddLabelTool(148, "B737", wx.Bitmap('E:/b737.bmp'))

        if ACCESS[USER][0] == "admin":
            self.toolbar.AddLabelTool(141, "B747", wx.Bitmap('E:/b747.bmp'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "VCH":
            self.toolbar.AddLabelTool(144, "AN26", wx.Bitmap('E:/an26.bmp'))

        if ACCESS[USER][0] == "admin":
            self.toolbar.AddLabelTool(143, "AN32", wx.Bitmap('E:/an32.bmp'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "VCH":
            self.toolbar.AddLabelTool(145, "AN72", wx.Bitmap('E:/an72.bmp'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "VCH":
            self.toolbar.AddLabelTool(146, "AN74", wx.Bitmap('E:/an74.bmp'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "gap_ukraine":
            self.toolbar.AddLabelTool(142, "AN148", wx.Bitmap('E:/an148.bmp'))

        if ACCESS[USER][0] == "admin":
            self.toolbar.AddLabelTool(147, "S340", wx.Bitmap('E:/s340.bmp'))

        #--------- HELP for toolbar bitmaps -----------------------------
        self.toolbar.SetToolLongHelp(133, "Open file containing flights")
        self.toolbar.SetToolLongHelp(136, "Open Compact Flash")
        self.toolbar.SetToolLongHelp(134, "Save chosen flight")
        #self.toolbar.SetToolLongHelp(135, "Save chosen flight in RAW format")
        self.toolbar.SetToolLongHelp(140, "A320. Choose data source.")
        self.toolbar.SetToolLongHelp(141, "B747. Choose data source.")
        self.toolbar.SetToolLongHelp(142, u"Aн148. Choose data source.")
        self.toolbar.SetToolLongHelp(143, u"Aн32. Choose data source.")
        self.toolbar.SetToolLongHelp(144, u"Aн26. Choose data source.")
        self.toolbar.SetToolLongHelp(145, u"Aн72. Choose data source.")
        self.toolbar.SetToolLongHelp(146, u"Aн74. Choose data source.")
        self.toolbar.SetToolLongHelp(147, "S340. Choose data source.")
        self.toolbar.SetToolLongHelp(148, "B737. Choose data source.")

        self.toolbar.AddSeparator()
        self.toolbar.Realize()

        # binding for toolbar
        self.Bind(wx.EVT_TOOL, self.on_choose, id=133)
        self.Bind(wx.EVT_TOOL, self.on_choose_cf, id=136)
        self.Bind(wx.EVT_MENU, self.a320_button, id=140)
        self.Bind(wx.EVT_MENU, self.b747_button, id=141)
        self.Bind(wx.EVT_MENU, self.an148_button, id=142)
        self.Bind(wx.EVT_MENU, self.an32_button, id=143)
        self.Bind(wx.EVT_MENU, self.an26_button, id=144)
        self.Bind(wx.EVT_MENU, self.an72_button, id=145)
        self.Bind(wx.EVT_MENU, self.an74_button, id=146)
        self.Bind(wx.EVT_MENU, self.s340_button, id=147)
        self.Bind(wx.EVT_MENU, self.b737_button, id=148)

    #---- At acft and data type selection via FILEMENU -> -------
    #---- selected option is stored
    def a320_qar_chosen(self, event):
        self.chosen_acft_type = 321

    def a320_cf_chosen(self, event):
        self.chosen_acft_type = 322

    def a320_fdr_chosen(self, event):
        self.chosen_acft_type = 323

    def b747_qar_chosen(self, event):
        self.chosen_acft_type = 331

    def an148_qar_chosen(self, event):
        self.chosen_acft_type = 341

    def an32_qar_chosen(self, event):
        self.chosen_acft_type = 351

    def an26_qar_chosen(self, event):
        self.chosen_acft_type = 361

    def an72_qar_chosen(self, event):
        self.chosen_acft_type = 371

    def an74_qar_chosen(self, event):
        self.chosen_acft_type = 381

    def s340_qar_chosen(self, event):
        self.chosen_acft_type = 391

    def b737_qar_chosen(self, event):
        self.chosen_acft_type = 401

    #---------------------------------------------------------------------
    #---- At acft and data type selection via TOOLBAR -> -------
    #---- When acft type ChoiceDialog is already opened ------------------
    #---- -> at picking type its value is stored -------------------------
    def a320_button(self, event):
        #---- In case acft type bitmap is pressed -> assign value of QAR --
        #---- as it is already marked in ChoiceDialog (as it first) -------
        self.chosen_acft_type = 321
        name = "A320"
        choices = ['QAR', 'Compact Flash']
        option = self.make_choice_window(name, choices)
        if option == "QAR":
            self.chosen_acft_type = 321
        elif option == "Compact Flash":
            self.chosen_acft_type = 322
        if option:
            # choose path to file
            self.on_choose_file()

    def b747_button(self, event):
        self.chosen_acft_type = 331
        name = "B747"
        choices = ['QAR']
        option = self.make_choice_window(name, choices)
        if option == "QAR":
            self.chosen_acft_type = 331
        if option:
            # choose path to file
            self.on_choose_file()

    def an148_button(self, event):
        self.chosen_acft_type = 341
        name = u"Aн148"
        choices = [u"БУР-92 А-05"]
        option = self.make_choice_window(name, choices)
        if option == u"БУР-92 А-05":
            self.chosen_acft_type = 341
        if option:
            # choose path to file
            self.on_choose_file()

    def an32_button(self, event):
        self.chosen_acft_type = 351
        name = u"Aн32"
        choices = [u"Тестер У3-2"]
        option = self.make_choice_window(name, choices)
        if option == u"Тестер У3-2":
            self.chosen_acft_type = 351
        if option:
            # choose path to file
            self.on_choose_file()

    def an26_button(self, event):
        self.chosen_acft_type = 361
        name = u"Aн26"
        choices = [u"МСРП-12"]
        option = self.make_choice_window(name, choices)
        if option == u"МСРП-12":
            self.chosen_acft_type = 361
        if option:
            # choose path to file
            self.on_choose_file()

    def an72_button(self, event):
        self.chosen_acft_type = 371
        name = u"Aн72"
        choices = [u"Тестер У3-2"]
        option = self.make_choice_window(name, choices)
        if option == u"Тестер У3-2":
            self.chosen_acft_type = 371
        if option:
            # choose path to file
            self.on_choose_file()

    def an74_button(self, event):
        self.chosen_acft_type = 381
        name = u"Aн74"
        choices = [u"БУР-3"]
        option = self.make_choice_window(name, choices)
        if option == u"БУР-3":
            self.chosen_acft_type = 381
        if option:
            # choose path to file
            self.on_choose_file()

    def s340_button(self, event):
        self.chosen_acft_type = 391
        name = "S340"
        choices = [u"QAR"]
        option = self.make_choice_window(name, choices)
        if option == u"QAR":
            self.chosen_acft_type = 391
        if option:
            # choose path to file
            self.on_choose_file()

    def b737_button(self, event):
        self.chosen_acft_type = 401
        name = "B737"
        choices = ['QAR', "FDR", "4700"]
        option = self.make_choice_window(name, choices)
        if option == "QAR":
            self.chosen_acft_type = 401
        elif option == "FDR":
            self.chosen_acft_type = 402
        elif option == "4700":
            self.chosen_acft_type = 403
        if option:
            # choose path to file
            self.on_choose_file()

    def make_choice_window(self, name, choices):
        dlg = wx.SingleChoiceDialog(self, '', name,
                                    choices, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
        else:  # Cancel button is pressed
            return False
        dlg.Destroy()
        return option

    def on_choose(self, event):
        self.chosen_acft_type = 0
        self.on_choose_file()

    #------------------------------------------------------------------
    def initialization(self, event):
        """ Flash initialization """
        window = InitializationFrame()
        # Show initialization window
        window.Show(True)

    #------------------------------------------------------------------
    def formatting(self, event):
        """ Flash formatting """
        dlg = wx.DirDialog(self, "Choose a Compact Flash:",
                           style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            path = u"%s" % dlg.GetPath()
        else:
            return
        dlg.Destroy()
        wait = wx.BusyInfo("Please wait, formatting...")
        f = FormatCompactFlash(path)
        del wait
        done_message = wx.MessageDialog(self, message="Formatting is over",
                                        caption="Fulfilment message",
                                        style=wx.OK | wx.CENTRE,
                                        pos=wx.DefaultPosition)
        done_message.ShowModal()
    #------------------------------------------------------------------

    def on_open_file(self, event):
        """Show Result status"""
        self.q = event.data
        self.qar_type = self.q.qar_type
        self.DestroyChildren()

        self.create_status_bar()

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.SetValue(50)

        #--------------THREADING-------------------------------------------
        self.statusbar.SetStatusText('Start loading')

        self.progress_bar.SetValue(50)
        self.progress_bar.SetValue(90)
        self.progress_bar.SetValue(100)

        self.create_tool_bar()

        panel = MyPanel(self, self.q, self.q.path)

        if panel.no_flights:
            self.statusbar.SetStatusText("There are no flights", 0)
            self.statusbar.SetStatusText("", 1)
        else:
            self.statusbar.SetStatusText("All flights are downloaded", 0)
            # display aircraft and recorder type
            try:
                self.statusbar.SetStatusText(u"%s-%s" %
                                            (self.acft_data_types[self.chosen_acft_type][0],
                                             self.acft_data_types[self.chosen_acft_type][1]),
                                             1)
            except KeyError:
                self.statusbar.SetStatusText(u" -%s" % self.qar_type, 1)

        self.sizer.Add(panel)
        self.sizer.Layout()

    def on_close(self, event):
        self.Destroy()

    def on_choose_file(self):
        """ Open a file"""
        dlg = wx.FileDialog(self, "Choose a directory:",
                            style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = u"%s" % dlg.GetPath()
        else:  # user pressed Cancel
            return

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.Pulse()

        self.statusbar.SetStatusText("Downloading...", 0)
        dlg.Destroy()
        if self.chosen_acft_type is None:
            self.flag = 0
        else:
            self.flag = self.chosen_acft_type
        self.q = WorkerThread(self, self.path, self.flag)

    def on_choose_cf(self, event):  # choose compact flash
        # In this case we include a "New directory" button.
        dlg = wx.DirDialog(self, "Choose a directory:",
                           style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            self.path = u"%s" % dlg.GetPath()
        else:
            return

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.Pulse()

        self.statusbar.SetStatusText("Downloading...", 0)
        dlg.Destroy()
        try:
            self.flag = 322
            self.q = WorkerThread(self, self.path, self.flag)
        except:
            pass

    def save_flight(self, event):
        self.save("flight")

    def save_raw(self, event):
        self.save("raw")

    def save(self, mode):
        self.get_path_to_save()
        self.progress_bar.Show()
        self.statusbar.SetStatusText("Saving...", 0)
        if self.chosen_acft_type is None:
            self.flag = "qar"
            acft = None
        else:
            self.flag = "%s_%s" % (self.acft_data_types[self.chosen_acft_type][0],
                                   self.acft_data_types[self.chosen_acft_type][1])
            acft = self.acft_data_types[self.chosen_acft_type][0]
        try:
            for each in self.selected:  # [flight_interval, index, date, qar]
                #if each in self.saved_flights:
                    #pass
                #else:
                # get flight start and end indexes
                separator = each[0].find(':')  # flight_interval
                start = int(each[0][:separator])
                end = int(each[0][separator + 1:])
                # as in list indexes go from 0
                flight_index = each[1] + 1
                flight_date = each[2]
                flight_qar = each[3]
                if acft:
                    flight_acft = acft
                else:
                    flight_acft = None
                #print(flight_acft)
                name = self.form_name(mode, flight_index, flight_acft,
                                        flight_qar, flight_date)
                #print(self.qar_type)
                f = Flight(self.progress_bar, start, end, self.q.path, name,
                            self.qar_type, self.path_to_save, self.flag)

                #self.saved_flights.append(each)
                #self.selected.remove(each)
        except AttributeError:  # save button was pressed, but no file was opened before
            self.warning("Open file with flights to process first")
            return
        self.selected = []

        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Flight is saved", 0)

    def warning(self, message, caption='Warning!'):
        dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def form_name(self, rec_type, index, acft, qar, date):
        cor_date = re.sub(r":", r"_", date)
        no_space_date = str(cor_date).replace(" ", "_")
        name = str(index) + "_" + str(acft) + "_" + str(qar) + "_" + str(no_space_date)
        if rec_type == "flight":
            return name
        elif rec_type == "raw":
            name_raw = name + "_raw"
            self.statusbar.SetStatusText("Raw file is exported", 0)
            return name_raw

    def get_path_to_save(self):
        save_dialog = wx.DirDialog(self, "Choose a directory to save file:",
                                   style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if save_dialog.ShowModal() == wx.ID_OK:
            self.path_to_save = save_dialog.GetPath()
        else:
            return
        save_dialog.Destroy()

#----------------------------------------------------------------------
# runs the script
app = wx.App(False)
frame = MyFrame()
app.MainLoop()