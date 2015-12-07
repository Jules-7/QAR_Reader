#-*-coding: utf-8-*-
import wx
import re
import os
import collections
from threading import Thread
import wx.lib.filebrowsebutton as filebrowse
from bur_92 import Bur4T
from raw_data_conversion import ReverseByte
from source_data import USER, QAR_TYPES, ACCESS, BUTTONS
from extractFlight import Flight
from splitter import Redirect
from datetime import datetime
from initialization import Initialize
from formatting import FormatCompactFlash
from converter import TwelveToSixteen, TenToSixteen
from harvard_digital import HarvardToDataConverter, ArincToDataConverter, LengthToDataConverter

""" This module:
    - creates window for choosing file with flights
    - displays all flights in file
    - allows to save flight as raw data or as flight according
      to QAR type
"""

# title for window depending on USER id
WIN_TITLE = ACCESS[USER][1]

# size of main window
SIZE = ACCESS[USER][2]

# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()
# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

ROOT_DIR = os.path.dirname(os.getcwd())


def event_result(win, func):
    """ Define Result Event """
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """ Simple event to carry arbitrary result data """
    def __init__(self, data):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class WorkerThread(Thread):  # Thread class that executes processing
    """ Worker Thread Class """
    def __init__(self, notify_window, path, chosen_acft_type, progress_bar):
        Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.path = path
        self.chosen_acft_type = chosen_acft_type
        self.progress_bar = progress_bar
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """ Run Worker Thread """
        # This is the code executing in the new thread
        out_instance = Redirect(self.path, self.chosen_acft_type, self.progress_bar)
        file_data = out_instance.result
        # Here's where the result would be returned
        wx.PostEvent(self._notify_window, ResultEvent(file_data))
        return


########################################################################
class MyPanel(wx.Panel):

    """ Panel to display flights in main window """

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
        # in case there are no flights in the file
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
                                    data.start_date[index].strftime('%H:%M:%S'))
            end_date = "%s %s" % (data.end_date[index].strftime('%d.%m.%Y'),
                                  data.end_date[index].strftime('%H:%M:%S'))
            seconds = data.durations[index]
            m, sec = divmod(seconds, 60)
            hours, minutes = divmod(m, 60)
            duration = "%02d h %02d m %02d s" % (hours, minutes, sec)
            # InsertStringItem provides creation of the next string
            # without it it is impossible to create the list
            self.list_ctrl.InsertStringItem(index, str(index + 1))
            self.list_ctrl.SetStringItem(index, 1, str(data.flights_start[index]))
            self.list_ctrl.SetStringItem(index, 2, start_date)
            self.list_ctrl.SetStringItem(index, 3, end_date)
            self.list_ctrl.SetStringItem(index, 4, duration)

            # associate index of the row with a particular flight
            self.flights_dict[index] = [flight, index, start_date, self.qar_type]
            index += 1

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 0, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)

    def on_item_selected(self, event):

        """ At the row selection - an index is returned
            using that index -> search the flight from the flights_dict
            and pass it for the processing """

        self.selected_parent_set = []
        self.parent.selected = []
        # -------- Ensures multiple flights selection -----------
        flight_number = self.list_ctrl.GetFirstSelected()
        self.selected_flight = [flight_number]
        while True:
            # check for another flight been chosen
            # in GetNextSelected(flight_number) -> the flight number
            # is given in order to look after this number
            item = self.list_ctrl.GetNextSelected(flight_number)
            if item == -1:  # no next choice
                break
            else:
                flight_number = item
                self.selected_flight.append(flight_number)
        for each in self.selected_flight:
            self.selected_parent_set.append(self.flights_dict[each])
        for choice in self.selected_parent_set:
            self.parent.selected.append(choice)
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
        self.flag = None

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
        flight_num_txt = wx.StaticText(self, -1, "Insert flight number", (2, 50))
        self.flight_num = wx.TextCtrl(self, -1, size=(140, -1))
        qar_num_txt = wx.StaticText(self, -1, "Insert QAR number", (2, 50))
        self.qar_num = wx.TextCtrl(self, -1, size=(140, -1))
        ok_button = wx.Button(self, id=1111, label="Ok")
        cancel_button = wx.Button(self, id=2222, label="Cancel")

        general_sizer = wx.BoxSizer(wx.VERTICAL)
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        qar_type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        date_sizer = wx.BoxSizer(wx.HORIZONTAL)
        flight_num_sizer = wx.BoxSizer(wx.HORIZONTAL)
        qar_num_sizer = wx.BoxSizer(wx.HORIZONTAL)
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

        flight_num_sizer.Add(flight_num_txt, 0, wx.ALL, 5)
        flight_num_sizer.Add(self.flight_num, 1, wx.ALL | wx.EXPAND, 5)

        qar_num_sizer.Add(qar_num_txt, 0, wx.ALL, 5)
        qar_num_sizer.Add(self.qar_num, 0, wx.ALL, 5)

        buttons_sizer.Add(ok_button, 0, wx.ALL, 5)
        buttons_sizer.Add(cancel_button, 0, wx.ALL, 5)

        general_sizer.Add(title_sizer, 0, wx.CENTER)
        general_sizer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(path_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(qar_type_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(date_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(flight_num_sizer, 0, wx.ALL | wx.EXPAND, 5)
        general_sizer.Add(qar_num_sizer, 0, wx.ALL | wx.EXPAND, 5)
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
            flight_n = self.flight_num.GetValue()
            self.flight_n = flight_n
        except AttributeError:
            self.flight_n = None
        try:
            qar_n = self.qar_num.GetValue()
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


class MyFrame(wx.Frame):

    """ Main frame that contains everything """

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "QAR Reader  %s" % WIN_TITLE, size=SIZE)
        # self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)  # vertical allows second toolbar be below the first one

        self.create_status_bar()
        # chosen_acft_type stands for both acft type and data source type
        # this is global like variable
        # it is used by almost all methods
        self.chosen_acft_type = None
        self.selected = []  # flights selected from the list
        # self.create_file_menu()
        self.create_tool_bar()

        self.saved_flights = []  # flights which are already processed and saved
        self.init_options = []
        self.optional_arg = None

        self.Show()
        event_result(self, self.on_open_file)
        self.SetSizer(self.sizer)

    def create_status_bar(self):
        """ Create StatusBar in the bottom of the window It contains text description (help info),
            information about aircraft type and QAR type, progress bar with progress status
        """
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)  # Set number of fields for statusbar
        self.statusbar.SetStatusWidths([-2, -1, 200])

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(2)
        self.progress_bar.SetPosition((rect.x + 2, rect.y + 2))
        self.progress_bar.SetSize((rect.width - 4, rect.height - 4))
        self.progress_bar.Hide()

    def create_tool_bar(self):

        """ Each user access is defined by access option - ability to see aircraft type buttons/file menu options
            Check of user ensures the display of this user options Access (visibility) of each option
            in file_menu and tool_bar is the same

            There are two toolbars. The second toolbar must be created after call of Realize() on the first one.
            Each toolbar contains its bitmaps - must be added to specific toolbar.

            At the end (after both toolbars are created), both must be added to frame sizer to stay fixed (no overflow)
            after the list of flights (panel) is shown

            !!! DO NOT !!! use this at window reload -> toolbar is not shown at first and
            then it appears on the top of the flights` data

            !!! NOTE !!! at executable creation -> images must be at the same folder with script

        """
        # ------------------- TOOLBAR 1 -------------------------------
        self.toolbar1 = wx.ToolBar(self)
        # self.toolbar = self.CreateToolBar()
        self.toolbar1.SetToolBitmapSize((30, 30))

        # ----------------- BITMAPS TOOLBAR 1 -----------------------------
        self.toolbar1.AddLabelTool(134, 'Save', wx.Bitmap('save.png'))
        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair":
            self.toolbar1.AddLabelTool(136, 'Open CF', wx.Bitmap('open_CF.png'))
            self.toolbar1.AddLabelTool(140, "A320", wx.Bitmap('a320.png'))
            self.toolbar1.AddLabelTool(147, "S340", wx.Bitmap('s340.png'))

        if (ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "yanair" or
            ACCESS[USER][0] == "bukovina" or ACCESS[USER][0] == "badr_airlines"):
            self.toolbar1.AddLabelTool(148, "B737", wx.Bitmap('b737.png'))

        if ACCESS[USER][0] == "admin":
            self.toolbar1.AddLabelTool(141, "B747", wx.Bitmap('b747.png'))
            self.toolbar1.AddLabelTool(143, "AN32", wx.Bitmap('an32.png'))
            self.toolbar1.AddLabelTool(151, "AN140", wx.Bitmap('an140.png'))
            self.toolbar1.AddLabelTool(150, "AN12", wx.Bitmap('an12.png'))
            self.toolbar1.AddLabelTool(157, "B767", wx.Bitmap('b767.png'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "VCH2269":
            self.toolbar1.AddLabelTool(144, "AN26", wx.Bitmap('an26.png'))
            self.toolbar1.AddLabelTool(145, "AN72", wx.Bitmap('an72.png'))
            self.toolbar1.AddLabelTool(146, "AN74", wx.Bitmap('an74.png'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "gap_ukraine":
            self.toolbar1.AddLabelTool(142, "AN148", wx.Bitmap('an148.png'))

        if ACCESS[USER][0] == "mak":
            self.toolbar1.AddLabelTool(152, "AN148", wx.Bitmap('bur92.png'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "il76":
            self.toolbar1.AddLabelTool(154, 'IL76', wx.Bitmap('il76.png'))

        if ACCESS[USER][0] == "admin" or ACCESS[USER][0] == "VCH1604":
            self.toolbar1.AddLabelTool(156, 'Mi24', wx.Bitmap('mi24.png'))

        # --------- HELP TOOLBAR 1 BITMAPS -----------------------------
        self.toolbar1.SetToolLongHelp(134, "Save chosen flight")
        self.toolbar1.SetToolLongHelp(133, "Open file containing flights")
        self.toolbar1.SetToolLongHelp(136, "Open Compact Flash")
        self.toolbar1.SetToolLongHelp(140, "A320. Choose data source")
        self.toolbar1.SetToolLongHelp(141, "B747. Choose data source")
        self.toolbar1.SetToolLongHelp(142, u"Aн148. Choose data source")
        self.toolbar1.SetToolLongHelp(143, u"Aн32. Choose data source")
        self.toolbar1.SetToolLongHelp(144, u"Aн26. Choose data source")
        self.toolbar1.SetToolLongHelp(145, u"Aн72. Choose data source")
        self.toolbar1.SetToolLongHelp(146, u"Aн74. Choose data source")
        self.toolbar1.SetToolLongHelp(147, "S340. Choose data source")
        self.toolbar1.SetToolLongHelp(148, "B737. Choose data source")
        self.toolbar1.SetToolLongHelp(150, u"Ан12. Choose data source")
        self.toolbar1.SetToolLongHelp(151, u"Ан140. Choose data source")
        self.toolbar1.SetToolLongHelp(152, u"БУР-92А-05. Choose data source")
        self.toolbar1.SetToolLongHelp(154, u"Ил76. Choose data source")
        self.toolbar1.SetToolLongHelp(156, u"Ми-24. Choose data source")
        self.toolbar1.SetToolLongHelp(157, "B767. Choose data source")

        self.toolbar1.AddSeparator()
        self.toolbar1.Realize()  # actually display toolbar
        # ------------------- END TOOLBAR 1 -------------------------------
        # -----------------------------------------------------------------

        # if it is admin mode - display additional toolbox with additional functionality
        if ACCESS[USER][0] == "admin":
            # ------------------- TOOLBAR 2 -----------------------------------
            self.toolbar2 = wx.ToolBar(self)  # create toolbar
            self.toolbar2.SetToolBitmapSize((30, 30))
            # -----------------------------------------------------------------

            # ----------------- BITMAPS TOOLBAR 2 -----------------------------

            self.toolbar2.AddLabelTool(135, 'Save RAW', wx.Bitmap('save_raw.png'))
            self.toolbar2.AddLabelTool(149, '12B->16B', wx.Bitmap('12_16.png'))
            self.toolbar2.AddLabelTool(155, '10B->16B', wx.Bitmap('10_16.png'))
            self.toolbar2.AddLabelTool(158, "swap", wx.Bitmap('swap.png'))
            self.toolbar2.AddLabelTool(153, 'har_dig', wx.Bitmap('harvard_data.png'))
            self.toolbar2.AddLabelTool(160, "length_arinc", wx.Bitmap('length_data.png'))
            self.toolbar2.AddLabelTool(159, "arinc_check", wx.Bitmap('arinc_data.png'))
            # -------------------------------------------------------------------

            # ----------------- HELP TOOLBAR 2 BITMAPS ---------------------------------
            self.toolbar2.SetToolLongHelp(135, "Save chosen flight in RAW format")
            self.toolbar2.SetToolLongHelp(149, "Convert from 12 bit-word to 16 bit-word")
            self.toolbar2.SetToolLongHelp(153, "Harvard -> Data: count pulses lengths, convert to arinc, record valid frames only")
            self.toolbar2.SetToolLongHelp(155, "Convert from 10 bit-word to 16 bit-word")
            self.toolbar2.SetToolLongHelp(158, "Swap bytes")
            self.toolbar2.SetToolLongHelp(159, "Arinc -> Data: record valid frames only")
            self.toolbar2.SetToolLongHelp(160, "Lengths -> Data: convert to arinc, record valid frames only")
            # ------------------------------------------------------------------------

            self.toolbar2.Realize()  # actually display toolbar

            # ------------------- END TOOLBAR 2 -------------------------------

        # -------------------- TOOLBARS EVENTS ----------------------------
        self.Bind(wx.EVT_TOOL, self.on_choose_file, id=133)
        self.Bind(wx.EVT_TOOL, self.save_flight, id=134)
        self.Bind(wx.EVT_TOOL, self.on_choose, id=133)
        self.Bind(wx.EVT_TOOL, self.save_raw, id=135)
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
        self.Bind(wx.EVT_MENU, self.twelve_to_sixteen, id=149)
        self.Bind(wx.EVT_MENU, self.an12_button, id=150)
        self.Bind(wx.EVT_MENU, self.an140_button, id=151)
        self.Bind(wx.EVT_MENU, self.an140_button, id=152)
        self.Bind(wx.EVT_MENU, self.harvard_to_data, id=153)
        self.Bind(wx.EVT_MENU, self.il76_button, id=154)
        self.Bind(wx.EVT_MENU, self.ten_to_sixteen, id=155)
        self.Bind(wx.EVT_MENU, self.mi24_button, id=156)
        self.Bind(wx.EVT_MENU, self.b767_button, id=157)
        self.Bind(wx.EVT_MENU, self.swap_button, id=158)
        self.Bind(wx.EVT_MENU, self.arinc_check, id=159)
        self.Bind(wx.EVT_MENU, self.length_to_data, id=160)
        # -------------------- END TOOLBARS EVENTS ----------------------------

        ''' for both toolbars to be static when the list of lights is shown -
            toolbars must be added to sizer here - at the end'''
        self.sizer.Add(self.toolbar1, 0, wx.EXPAND)

        if ACCESS[USER][0] == "admin": #  if it is admin - add second toolbar
            if self.toolbar2:
                self.sizer.Add(self.toolbar2, 0, wx.EXPAND)

    # ---------------------------------------------------------------------
    # ---- At the acft and data type selection via TOOLBAR ->
    # ---- When acft type ChoiceDialog is already opened
    # ---- -> at type picking its value is stored
    # ---- In case the acft type bitmap is pressed -> assign value of first option
    # ---- as it is already marked in the ChoiceDialog (as it is the first one)
    def choose_acft_qar_onclick_button(self, button_type):
        name = button_type["name"]  # choice window name
        # use orderdict, so each time keys are of the same order
        choices_dict = collections.OrderedDict(sorted(button_type["choices"].items()))
        choices_list = [key for key, value in choices_dict.iteritems()]
        option = self.make_choice_window(name, choices_list)
        if option:  # obtain choice
            self.chosen_acft_type = choices_dict[option]
        else:  # if nothing was chosen - select default type
            self.chosen_acft_type = button_type['default_choice']
        if self.chosen_acft_type == 383:  # bur-3 analog
            self.optional_arg = self.get_zero_length()  # get zero for conversion
        if option:  # choose a path to file
            self.on_choose_file()

    def a320_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["a320"])

    def b747_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["b747"])

    def an148_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an148"])

    def an140_button(self, event):
        option = None
        self.chosen_acft_type = 421
        name = u"Aн140"
        if ACCESS[USER][0] == "admin":
            choices = [u"БУР-92А-05"]
            option = self.make_choice_window(name, choices)
            if option == u"БУР-92А-05":
                self.chosen_acft_type = 421
        elif ACCESS[USER][0] == "mak":
            option = u"БУР-92А-05"
        if option:  # choose path to file
            self.on_choose_file()

    def an32_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an32"])

    def an26_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an26"])

    def an72_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an72"])

    def an74_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an74"])

    def s340_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["s340"])

    def b737_button(self, event):
        self.chosen_acft_type = 401
        name = "B737"
        choices = []
        if ACCESS[USER][0] == "admin":
            choices = ["QAR (arinc)", "DFDR 980", "DFDR 980 I", "QAR 4700 (analog)", "QAR 4700", "QAR NG"]
        elif ACCESS[USER][0] == "yanair":
            choices = ["DFDR 980", "QAR 4700"]
        elif ACCESS[USER][0] == "bukovina":
            choices = ["DFDR 980 I"]
        elif ACCESS[USER][0] == "badr_airlines":
            choices = ["DFDR 980"]
        option = self.make_choice_window(name, choices)
        if option == "QAR (arinc)":  # save this file with extension .inf to target place
            self.chosen_acft_type = 401
            self.get_path_to_file()
            if self.path:
                self.get_path_to_save()
                flight = Flight(self.progress_bar, start=None, end=None, path=self.path,
                                name=None, chosen_acft_type=self.chosen_acft_type,
                                path_to_save=self.path_to_save)
        elif option == "DFDR 980":  # different fdr types
            dfdr_choices = ["default", "BDB", "BDO", "BDV"]
            dfdr_type = self.make_choice_window(name, dfdr_choices)
            if dfdr_type == "default":
                self.chosen_acft_type = 402
            elif dfdr_type == "BDB":
                self.chosen_acft_type = 4031
            elif dfdr_type == "BDO":
                self.chosen_acft_type = 4032
            elif dfdr_type == "BDV":
                self.chosen_acft_type = 4033
        elif option == "DFDR 980 I":
            self.chosen_acft_type = 4022
        elif option == "QAR 4700 (analog)":
            self.chosen_acft_type = 403
            zero = self.get_zero_length()  # get zero for conversion
            direction = self.get_arinc_direction()
            self.optional_arg = [zero, direction[:1]]
        elif option == "QAR 4700":
            self.chosen_acft_type = 4034
        elif option == "QAR NG":
            self.chosen_acft_type = 404
        if option:
            self.on_choose_file()

    def an12_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["an12"])

    def il76_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["il76"])

    def b767_button(self, event):
        self.choose_acft_qar_onclick_button(BUTTONS["b767"])

    def make_choice_window(self, name, choices):
        dlg = wx.SingleChoiceDialog(self, '', name,
                                    choices, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
        else:  # Cancel button has been pressed
            return False
        dlg.Destroy()
        return option

    def on_choose(self, event):
        self.chosen_acft_type = 0
        self.on_choose_file()

    # ------------------------------------------------------------------
    def initialization(self, event):

        """ Display initialization options for a flash-card """

        window = InitializationFrame()
        # Show initialization window
        window.Show(True)

    # ------------------------------------------------------------------
    def formatting(self, event):

        """ Perform formatting of a flash-card"""

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
    # ------------------------------------------------------------------

    def on_open_file(self, event):

        """ Show Result status """

        self.file_data = event.data
        self.qar_type = self.file_data.qar_type
        self.DestroyChildren()

        self.create_status_bar()

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.SetValue(50)

        # --------------THREADING-------------------------------------------
        self.statusbar.SetStatusText('Start loading')

        self.progress_bar.SetValue(50)
        self.progress_bar.SetValue(90)
        self.progress_bar.SetValue(100)

        self.create_tool_bar()

        # at this point separate thread starts and perform processing
        panel = MyPanel(self, self.file_data, self.file_data.path)

        if panel.no_flights:
            self.statusbar.SetStatusText("There are no flights", 0)
            self.statusbar.SetStatusText("", 1)
        else:
            self.statusbar.SetStatusText("All flights are downloaded", 0)
            # display aircraft and recorder type
            try:
                self.statusbar.SetStatusText(u"%s-%s" %
                                            (QAR_TYPES[self.chosen_acft_type][0],
                                             QAR_TYPES[self.chosen_acft_type][1]),
                                             1)
            except KeyError:
                self.statusbar.SetStatusText(u" -%s" % self.qar_type, 1)

        self.sizer.Add(panel)
        self.sizer.Layout()

    def on_close(self, event):
        self.Destroy()

    def on_choose_file(self):

        """ Open a file which contain flights"""

        self.get_path_to_file()
        # redirect path and choice of acft/qar for file opening
        # and flight displaying
        try:
            self.file_data = WorkerThread(self, self.path,
                                          self.chosen_acft_type,
                                          self.progress_bar)
            self.progress_bar.Show()
            self.progress_bar.SetValue(10)
            self.statusbar.SetStatusText("Downloading...", 0)

        except AttributeError:
            self.statusbar.SetStatusText("No file is selected...", 0)

    def on_choose_cf(self, event):  # choose compact flash
        self.get_path_to_dir()

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.SetValue(15)
        self.progress_bar.SetValue(20)

        dlg_save = wx.DirDialog(self, "Choose directory to get flight copy",
                                style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg_save.ShowModal() == wx.ID_OK:
            path_save = u"%s" % dlg_save.GetPath()
            self.path += '__save__'
            self.path += path_save
            print(self.path)
        else:
            return

        self.progress_bar.Pulse()

        self.statusbar.SetStatusText("Downloading...", 0)

        try:
            self.chosen_acft_type = 322
            self.file_data = WorkerThread(self, self.path,
                                          self.chosen_acft_type,
                                          self.progress_bar)
        except:
            pass

    def save_flight(self, event):
        if not self.chosen_acft_type:
            self.warning("Chose file to load first")
            return
        self.save("flight")

    def save_raw(self, event):
        self.save("raw")

    def save(self, mode):
        self.get_path_to_save()
        self.progress_bar.Show()
        self.statusbar.SetStatusText("Saving...", 0)
        try:
            for each in self.selected:  # [flight_interval, index, date, qar]
                # get flight start and end indexes
                separator = each[0].find(':')  # flight_interval
                start = int(each[0][:separator])
                end = int(each[0][separator + 1:])
                # as in list indexes go from 0
                flight_index = each[1] + 1
                flight_date = each[2]
                name = self.form_name(mode, flight_index, flight_date)
                flight = Flight(self.progress_bar, start, end, self.file_data.path,
                                name, self.chosen_acft_type, self.path_to_save,
                                self.optional_arg)

        except AttributeError:  # save button is pressed, but no file was opened before
            self.warning("Open file with flights to process")
            return
        self.selected = []

        #self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Flight is saved", 0)

    def twelve_to_sixteen(self, event):

        """ Transform data recorded as 12 bits word into 16 bits data;
            take what is and just add convert all data (no check for header)"""

        self.get_path_to_file()
        self.get_path_to_save()
        self.progress_bar.Show()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = TwelveToSixteen(self.path, self.path_to_save, self.progress_bar)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def ten_to_sixteen(self, event):

        """ Transform data recorded as 10 bits word into 16 bits data;
            take what is in it, just add zeroes and record back (no check for header)"""

        self.get_path_to_file()
        self.get_path_to_save()
        self.progress_bar.Show()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = TenToSixteen(self.path, self.path_to_save, self.progress_bar)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def harvard_to_data(self, event):
        """ Transform rectangular Harvard data to arinc """
        self.get_path_to_file()
        self.get_file_to_save()
        zero_length = self.get_zero_length()
        direction = self.get_arinc_direction()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = HarvardToDataConverter(self.path, zero_length, self.progress_bar, self.path_to_save, direction)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def arinc_check(self, event):
        """ Search in arinc digital data for valid arinc packets """
        self.get_path_to_file()
        self.get_file_to_save()
        direction = self.get_arinc_direction()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = ArincToDataConverter(self.path, self.progress_bar, self.path_to_save, direction)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def length_to_data(self, event):
        """ Convert already calculated length to arinc """
        self.get_path_to_file()
        self.get_file_to_save()
        zero_length = self.get_zero_length()
        direction = self.get_arinc_direction()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = LengthToDataConverter(self.path, zero_length, self.progress_bar, self.path_to_save, direction)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def swap_button(self, event):
        """ Take byte and reverse it """
        self.get_path_to_file()
        self.get_file_to_save()
        self.progress_bar.Show()
        self.statusbar.SetStatusText("Converting...", 0)
        convert = ReverseByte(self.path, self.progress_bar, self.path_to_save)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Conversion is finished", 0)

    def mi24_button(self, event):
        """ Open raw flight to convert it in flight with valid frames only and
            convert from 10 bit words to 16 bit words  """
        self.chosen_acft_type = BUTTONS["mi24"]["default_choice"]
        self.get_path_to_file()
        self.get_path_to_save()
        process_flight = Bur4T(self.path, self.chosen_acft_type, self.progress_bar, self.path_to_save)
        self.progress_bar.SetValue(100)
        self.statusbar.SetStatusText("Flight processing is finished", 0)

    def warning(self, message, caption='Warning!'):
        dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def form_name(self, rec_type, index, date):
        """
           - either add 'raw' record or not
           - add flight index/number and date it was performed
           - add acft and qar type from self.chosen_acft_type 'global' variable """
        cor_date = re.sub(r":", r"_", date)
        no_space_date = str(cor_date).replace(" ", "_")
        acft = QAR_TYPES[self.chosen_acft_type][0]
        qar = QAR_TYPES[self.chosen_acft_type][1]
        if acft == "s340":
            qar = "qar"
        if ACCESS[USER][0] == "mak":
            name = str(index) + "_" + str(qar) + "_" + str(no_space_date)
        else:
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
            self.path_to_save = u"%s" % save_dialog.GetPath()
        else:
            return
        save_dialog.Destroy()

    def get_file_to_save(self):
        """ Get path and name for file to save """
        save_dialog = wx.FileDialog(self, "Save file as: ", "", "",
                    "INF files (*.inf)| *.inf | BIN files (*.bin)| *.bin | DAT files (*.dat) | *.dat",
                    wx.FD_SAVE)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if save_dialog.ShowModal() == wx.ID_OK:
            self.path_to_save = u"%s" % save_dialog.GetPath()
        else:
            return
        save_dialog.Destroy()

    def get_path_to_file(self):
        dlg = wx.FileDialog(self, "Choose a file:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = u"%s" % dlg.GetPath()
        else:  # user pressed Cancel
            return
        dlg.Destroy()

    def get_path_to_dir(self):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            self.path = u"%s" % dlg.GetPath()
        else:
            return
        dlg.Destroy()

    def get_zero_length(self):
        dlg = wx.TextEntryDialog(self, 'Insert zero length')
        if dlg.ShowModal() == wx.ID_OK:
            zero_length = dlg.GetValue()
            dlg.Destroy()
            return int(zero_length)
        else:
            dlg.Destroy()
            return


    def get_arinc_direction(self):
        choices = ["Direct", "Reverse"]
        dlg = wx.SingleChoiceDialog(self, '', "Insert direction for ARINC words search",
                                    choices, wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
        else:  # Cancel button has been pressed
            return False
        dlg.Destroy()
        return option[:1]


# ----------------------------------------------------------------------
# this piece of code runs the script
app = wx.App(False)
frame = MyFrame()
app.MainLoop()
