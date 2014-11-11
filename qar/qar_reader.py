#-*-coding: utf-8-*-
from threading import *
import wx
import re
import time
from pickFlight_v5 import Flight
from splitter import Split
from datetime import datetime
from initialization import Initialize
import wx.lib.filebrowsebutton as filebrowse
from wx.lib.masked import TimeCtrl
"""this module:
- creates window for choosing of file with flights
- displays all flights in file
- allows to save flight as raw data or as flight according
to QAR type"""

# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()
# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()


def EVT_RESULT(win, func):
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
    """Panel to display flights in main window"""
    #----------------------------------------------------------------------
    def __init__(self, parent, data, path):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.path = path
        self.qar_type = data.qar_type
        self.selected_flight = []
        self.selected_parent_set = []

        self.list_ctrl = wx.ListCtrl(self,
                                     style=wx.LC_REPORT
                                     | wx.BORDER_SUNKEN,
                                     size=(2000, 2000))  # list of items with scroll
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.list_ctrl.InsertColumn(0, u"Flight №", width=70)
        self.list_ctrl.InsertColumn(1, "ID", width=100)
        self.list_ctrl.InsertColumn(2, "Start date", width=140)
        self.list_ctrl.InsertColumn(3, "End date", width=140)
        self.list_ctrl.InsertColumn(4, "Duration", width=100)

        index = 0
        self.flights_dict = {}

        for each in data.flight_intervals:
            try:
                flight = str(data.flight_intervals[index][0]) + ":" + str(data.flight_intervals[index][1])
            except IndexError:
                flight = str(data.flight_intervals[index][0]) + ":" + str(0)

            start_date = "%s %s" % (data.start_date[index].strftime('%d.%m.%Y'),
                                    data.start_date[index].time())
            end_date = "%s %s" % (data.end_date[index].strftime('%d.%m.%Y'),
                                  data.end_date[index].time())
            # flight duration
            #duration = data.durations[index]
            duration = time.strftime('%H h %M m %S s', time.gmtime(data.durations[index]))
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

        self.parent.statusbar.SetStatusText("All flights are downloaded. ", 0)
        self.parent.statusbar.SetStatusText("%s" % data.qar_type, 1)

    #----------------------------------------------------------------------
    def on_item_selected(self, event):
        ''' at row selection - index is returned
        using that index search for flight from flights_dict
        and pass it for processing '''
        #-------- Ensures multiple flights selection -----------
        self.selected_flight.append(event.m_itemIndex)
        #print('selected flights %s ' % self.selected_flight)
        for each in self.selected_flight:
            self.selected_parent_set.append(self.flights_dict[each])
        chosen_flights = [each[0] for each in self.selected_parent_set]
        unique_elements = list(set(chosen_flights))
        for element in unique_elements:
            for choice in self.selected_parent_set:
                if element == choice[0]:
                    self.parent.selected.append(choice)
        #print("selected to parent %s " % self.parent.selected)
        self.parent.progress_bar.Hide()


class InitializationFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Initialization settings", size=(400, 350))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = InitializationPanel(self)
        self.sizer.Add(panel)
        self.sizer.Layout()


class InitializationPanel(wx.Panel):
    """Panel to display Initialization settings menu"""
    #----------------------------------------------------------------------
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.drive = None
        self.qar_type = None
        self.date = datetime.today()
        self.time = datetime.now().strftime('%H:%M:%S')
        self.flight_n = None
        self.qar_n = None

        title = wx.StaticText(self, -1, "Please choose options for initialization")
        path_to_drive = filebrowse.DirBrowseButton(self, -1, size=(350, -1),
                                                   changeCallback = self.get_drive,
                                                   labelText="Choose a drive")

        qar_type_list = ['A320 - QAR',
                         'A320 - Compact Flash',
                         'B747 - QAR',
                         'An148 - BUR-92',
                         'QAR-4XXX']

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
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, wx.ID_ANY, "QAR Reader", size=(600, 500))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_bar()
        self.chosen_acft_type = None  # means both acft type and data source type
        self.acft_data_types = {321: "a320_qar",
                                322: "a320_cf",
                                323: "a320_fdr",
                                331: "b747_qar",
                                341: "an148_qar"}
        self.selected = []  # flights selected from list
        self.file_menu()
        self.tool_bar()
        self.saved_flights = []  # flights which are already processed and saved
        self.init_options = []

        self.Show()
        EVT_RESULT(self, self.on_result)
        self.SetSizer(self.sizer)

    def status_bar(self):
        #------------------------CREATE STATUSBAR---------------------------------
        self.statusbar = self.CreateStatusBar()   # Create StatusBar in the bottom of the window
        self.statusbar.SetFieldsCount(3)  # Set number of fields in statusbar
        self.statusbar.SetStatusWidths([-2, -1, 200])

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(2)
        self.progress_bar.SetPosition((rect.x + 2, rect.y + 2))
        self.progress_bar.SetSize((rect.width - 4, rect.height - 4))
        self.progress_bar.Hide()

    def file_menu(self):
        #-------------------------CREATE FILEMENU-------------------------------------

        filemenu = wx.Menu()
        choose_file = filemenu.Append(301, "&Choose", " Choose file to open")
        choose_cf = filemenu.Append(302, "&Choose Compact Flash", " Choose Compact Flash to open")
        menu_exit = filemenu.Append(wx.ID_EXIT, "&Exit", " Terminate the program")
        initialize = filemenu.Append(wx.ID_ANY, "&Initialize", " Initialize QAR")
        filemenu.AppendSeparator()

        savemenu = wx.Menu()
        save_file = savemenu.Append(311, "&Save", " Safe flight")
        save_raw_file = savemenu.Append(312, "&Save RAW", " Save raw data")
        savemenu.AppendSeparator()

        a320menu = wx.Menu()
        a320_qar = a320menu.Append(321, "&QAR", "Process data from QAR")
        a320_cf = a320menu.Append(322, "&Compact Flash", " Process data from compact flash")
        a320_fdr = a320menu.Append(323, "&FDR RAW", " Process data from FDR in RAW format")
        a320menu.AppendSeparator()

        b747menu = wx.Menu()
        b747_qar = b747menu.Append(331, "&QAR", "Process data from QAR")
        b747menu.AppendSeparator()

        an148menu = wx.Menu()
        an148_qar = an148menu.Append(341, "&QAR", "Process data from QAR")

        menubar = wx.MenuBar()  # Creating the menubar
        menubar.Append(filemenu, "&File")  # Adding the "filemenu" to the MenuBar
        menubar.Append(savemenu, "&Save")  # Adding the "savemenu" to the MenuBar
        menubar.Append(a320menu, "&A320")
        menubar.Append(b747menu, "&B747")
        menubar.Append(an148menu, "&AN148")
        self.SetMenuBar(menubar)  # Adding the MenuBar to the Frame content.

        #--------- Bindings of buttons/commands with methods
        self.Bind(wx.EVT_TOOL, self.on_choose_file, id=133)  # bind with toolbar
        self.Bind(wx.EVT_MENU, self.on_choose_file, choose_file)  # bind with filemenu
        self.Bind(wx.EVT_TOOL, self.on_choose_cf, id=136)
        self.Bind(wx.EVT_MENU, self.on_choose_cf, choose_cf)
        self.Bind(wx.EVT_TOOL, self.save_flight, id=134)
        self.Bind(wx.EVT_MENU, self.save_flight, save_file)
        self.Bind(wx.EVT_TOOL, self.save_raw, id=135)
        self.Bind(wx.EVT_MENU, self.save_raw, save_raw_file)
        self.Bind(wx.EVT_MENU, self.on_close, menu_exit)
        self.Bind(wx.EVT_MENU, self.initialization, initialize)

        self.Bind(wx.EVT_MENU, self.a320_qar_chosen, a320_qar)
        self.Bind(wx.EVT_TOOL, self.a320_cf_chosen, a320_cf)
        self.Bind(wx.EVT_TOOL, self.a320_fdr_chosen, a320_fdr)
        self.Bind(wx.EVT_TOOL, self.b747_qar_chosen, b747_qar)
        self.Bind(wx.EVT_TOOL, self.an148_qar_chosen, an148_qar)

        self.Bind(wx.EVT_MENU, self.a320_button, id=140)
        self.Bind(wx.EVT_MENU, self.b747_button, id=141)
        self.Bind(wx.EVT_MENU, self.an148_button, id=142)

    #---- At acft and data type selection via filemenu -> -------
    #---- selected option is stored
    def a320_qar_chosen(self, event):
        self.chosen_acft_type = 321
        #print(self.chosen_acft_type)

    def a320_cf_chosen(self, event):
        self.chosen_acft_type = 322
        #print(self.chosen_acft_type)

    def a320_fdr_chosen(self, event):
        self.chosen_acft_type = 323
        #print(self.chosen_acft_type)

    def b747_qar_chosen(self, event):
        self.chosen_acft_type = 331
        #print(self.chosen_acft_type)

    def an148_qar_chosen(self, event):
        self.chosen_acft_type = 341
        #print(self.chosen_acft_type)

    #---- When acft type ChoiceDialog is already opened ------------------
    #---- -> at picking type its value is stored -------------------------
    def a320_button(self, event):
        #---- In case acft type bitmap is pressed -> assign value of QAR --
        #---- as it is already marked in ChoiceDialog (as it first) -------
        self.chosen_acft_type = 321
        dlg = wx.SingleChoiceDialog(self, '', "A320", ['QAR', 'Compact Flash', 'FDR'])
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
            if option == "QAR":
                self.chosen_acft_type = 321
            elif option == "Compact Flash":
                self.chosen_acft_type = 322
            elif option == "FDR":
                self.chosen_acft_type = 323
            #print(self.chosen_acft_type)
        else:
            return
        dlg.Destroy()

    def b747_button(self, event):
        self.chosen_acft_type = 331
        dlg = wx.SingleChoiceDialog(self, '', "B747", ['QAR'],
                                    wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
            if option is "QAR":
                self.chosen_acft_type = 331
            #print(self.chosen_acft_type)
        else:
            return
        dlg.Destroy()

    def an148_button(self, event):
        self.chosen_acft_type = 341
        dlg = wx.SingleChoiceDialog(self, '', "AN148", ['QAR'],
                                    wx.CHOICEDLG_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            option = dlg.GetStringSelection()
            if option is "QAR":
                self.chosen_acft_type = 341
            #print(self.chosen_acft_type)
        else:
            return
        dlg.Destroy()

    def initialization(self, event):
        # Show initialization window
        window = InitializationFrame()
        window.Show(True)

    def tool_bar(self):
        #-----------------------CREATE TOOLBAR----------------------------------------
        # do not use this at window reload -> toolbar is not a=show at first and
        # then it appears on top of flights data
        #self.toolbar = wx.ToolBar(self, -1)
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((30, 30))
        #---------- at executable creation -> place images to the same folder and change path
        self.toolbar.AddLabelTool(133, 'Open', wx.Bitmap('E:/open_folder.png'))
        self.toolbar.AddLabelTool(136, 'Open CF', wx.Bitmap('E:/open_CF.png'))
        self.toolbar.AddLabelTool(134, 'Save', wx.Bitmap('E:/save.png'))
        self.toolbar.AddLabelTool(135, 'Save RAW', wx.Bitmap('E:/save_raw.png'))
        self.toolbar.AddLabelTool(140, "A320", wx.Bitmap('E:/a320.png'))
        self.toolbar.AddLabelTool(141, "B747", wx.Bitmap('E:/b747.png'))
        self.toolbar.AddLabelTool(142, "AN148", wx.Bitmap('E:/an148.png'))

        #--------- HELP for toolbar bitmaps ------------------------------
        self.toolbar.SetToolLongHelp(133, "Open file containing flights")
        self.toolbar.SetToolLongHelp(136, "Open Compact Flash")
        self.toolbar.SetToolLongHelp(134, "Save chosen flight")
        self.toolbar.SetToolLongHelp(135, "Save chosen flight in RAW format")
        self.toolbar.SetToolLongHelp(140, "A320. Chose data source.")
        self.toolbar.SetToolLongHelp(141, "B747. Chose data source.")
        self.toolbar.SetToolLongHelp(142, "AN148. Chose data source.")

        self.toolbar.AddSeparator()
        self.toolbar.Realize()

    def on_result(self, event):
        """Show Result status"""
        self.q = event.data
        self.qar_type = self.q.qar_type
        self.DestroyChildren()

        self.status_bar()

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        self.progress_bar.SetValue(50)

        #--------------THREADING-------------------------------------------
        self.statusbar.SetStatusText('Start loading')

        self.progress_bar.SetValue(50)
        self.progress_bar.SetValue(90)
        self.progress_bar.SetValue(100)

        self.tool_bar()

        panel = MyPanel(self, self.q, self.q.path)

        self.statusbar.SetStatusText(self.qar_type, 2)

        self.sizer.Add(panel)
        self.sizer.Layout()

    def on_close(self, event):
        self.Destroy()

    def on_choose_file(self, event):
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
            self.flag = "qar"
        else:
            self.flag = self.acft_data_types[self.chosen_acft_type]
        try:
            self.q = WorkerThread(self, self.path, self.flag)
        except:
            pass

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
            self.flag = "a320_cf"
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
        if self.chosen_acft_type is None:
            self.flag = "qar"
            acft = None
        else:
            self.flag = self.acft_data_types[self.chosen_acft_type]
            acft_index = self.flag.find("_")
            acft = self.flag[:acft_index]
        try:
            for each in self.selected:  # [flight_interval, index, date, qar]
                if each in self.saved_flights:
                    pass
                else:
                    # get flight start and end indexes
                    separator = each[0].find(':')  # flight_interval
                    start = int(each[0][:separator])
                    end = int(each[0][separator + 1:])
                    flight_index = each[1] + 1
                    flight_date = each[2]
                    flight_qar = each[3]
                    if acft:
                        flight_acft = acft
                    else:
                        flight_acft = None
                    name = self.form_name(mode, flight_index, flight_acft, flight_qar,flight_date)

                    f = Flight(self.progress_bar, start, end, self.q.path, name, self.qar_type,
                               self.path_to_save, self.flag)
                    self.saved_flights.append(each)
        except AttributeError:
            self.warning("Open file with flights to process first")
            return
        self.selected = []
        self.progress_bar.SetValue(100)

    def warning(self, message, caption='Warning!'):
        dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def form_name(self, rec_type, index, acft, qar, date):
        cor_date = re.sub(r":", r"_", date)
        no_space_date = str(cor_date).replace(" ", "_")
        name = str(index) + "_" + str(acft) + "_" + str(qar) + "_" + str(no_space_date)
        if rec_type == "flight":
            self.statusbar.SetStatusText("Flight is exported", 0)
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
            #print(self.path_to_save)
        else:
            return     # the user changed idea...

        save_dialog.Destroy()

#----------------------------------------------------------------------
# runs the script
app = wx.App(False)
frame = MyFrame()
app.MainLoop()