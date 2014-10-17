#-*-coding: utf-8-*-
from threading import *
import wx
import datetime
from qarReader_prod_v2 import QARReader
from pickFlight_v5 import Flight
from splitter import Split

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

        self.list_ctrl = wx.ListCtrl(self,
                                     style=wx.LC_REPORT
                                     |wx.BORDER_SUNKEN,
                                     size=(2000, 2000))  # list of items with scroll
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.list_ctrl.InsertColumn(0, "ID", width=100)
        self.list_ctrl.InsertColumn(1, "Start date", width=140)
        self.list_ctrl.InsertColumn(2, "End date", width=140)
        self.list_ctrl.InsertColumn(3, "Duration", width=100)

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
            duration = data.durations[index]  # flight duration

            #InsertStringItem provides creation of next string
            #without it impossible to create list
            self.list_ctrl.InsertStringItem(index, str(data.flights_start[index]))
            self.list_ctrl.SetStringItem(index, 1, start_date)
            self.list_ctrl.SetStringItem(index, 2, end_date)
            self.list_ctrl.SetStringItem(index, 3, duration)

            #associate index of row with particular flight
            self.flights_dict[index] = flight
            index += 1

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 0, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer)

        self.parent.statusbar.SetStatusText("All flights are downloaded. "
                                            "QAR type is %s" % data.qar_type, 0)

    #----------------------------------------------------------------------
    def on_item_selected(self, event):
        ''' at row selection - index is returned
        using that index search for flight from flights_dict
        and pass it for processing '''
        selected_flight = event.m_itemIndex
        self.parent.selected = self.flights_dict[selected_flight]

        self.parent.progress_bar.Hide()


########################################################################
class MyFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, wx.ID_ANY, "QAR", size=(500, 400))

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_bar()
        self.selected = None
        self.file_menu()
        self.tool_bar()

        self.Show()

        EVT_RESULT(self, self.OnResult)

        self.SetSizer(self.sizer)

    def status_bar(self):
        #------------------------CREATE STATUSBAR---------------------------------
        self.statusbar = self.CreateStatusBar()   # Create StatusBar in the bottom of the window
        self.statusbar.SetFieldsCount(2)  # Set number of fields in statusbar
        self.statusbar.SetStatusWidths([320, -1])

        self.progress_bar = wx.Gauge(self.statusbar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        rect = self.statusbar.GetFieldRect(1)
        self.progress_bar.SetPosition((rect.x + 2, rect.y + 2))
        self.progress_bar.SetSize((rect.width - 4, rect.height - 4))
        self.progress_bar.Hide()

    def file_menu(self):
        #-------------------------CREATE FILEMENU-------------------------------------
        filemenu = wx.Menu()  # Setting up the menu
        choose_file = filemenu.Append(wx.ID_ANY, "&Choose", " Choose file to open")
        choose_cf = filemenu.Append(wx.ID_ANY, "&Choose Compact Flash", "Choose Compact Flash")
        save_file = filemenu.Append(wx.ID_ANY, "&Save", " Safe flight")
        save_raw_file = filemenu.Append(wx.ID_ANY, "&Save RAW", " Save raw data")
        menu_exit = filemenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        menubar = wx.MenuBar()  # Creating the menubar
        menubar.Append(filemenu, "&File")  # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menubar)  # Adding the MenuBar to the Frame content.

        self.Bind(wx.EVT_TOOL, self.on_choose_file, id=133)
        self.Bind(wx.EVT_MENU, self.on_choose_file, choose_file)
        self.Bind(wx.EVT_TOOL, self.save, id=134)
        self.Bind(wx.EVT_MENU, self.save, save_file)
        self.Bind(wx.EVT_TOOL, self.save_raw, id=135)
        self.Bind(wx.EVT_MENU, self.save_raw, save_raw_file)
        self.Bind(wx.EVT_MENU, self.on_close, menu_exit)
        self.Bind(wx.EVT_TOOL, self.on_choose_cf, id=136)
        self.Bind(wx.EVT_MENU, self.on_choose_cf, choose_cf)
        #self.Bind(wx.EVT_BUTTON, self.OnButton, b)

    def tool_bar(self):
        #-----------------------CREATE TOOLBAR----------------------------------------
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((32,32))
        self.toolbar.AddLabelTool(133, 'Open', wx.Bitmap('E:/open_folder.png'))
        self.toolbar.AddLabelTool(134, 'Save', wx.Bitmap('E:/save.png'))
        self.toolbar.AddLabelTool(135, 'Save RAW', wx.Bitmap('E:/save_raw.png'))
        self.toolbar.AddLabelTool(136, 'Open CF', wx.Bitmap('E:/open_CF.png'))
        #b = wx.Button(self, -1, "Create and Show a DirDialog", (50,50))
        #self.toolbar.AddLabelTool(3, '', wx.Bitmap('GUI/icons/close.png'))
        self.toolbar.AddSeparator()
        self.toolbar.Realize()

    def OnResult(self, event):
        """Show Result status"""
        self.q = event.data
        self.qar_type = self.q.qar_type
        self.DestroyChildren()

        self.status_bar()

        self.progress_bar.Show()
        self.progress_bar.SetValue(10)
        #self.progress_bar.Pulse()
        self.progress_bar.SetValue(50)
        #self.sizer.Layout()

        #--------------THREADING-------------------------------------------
        self.statusbar.SetStatusText('Start loading')

        self.progress_bar.SetValue(50)
        self.progress_bar.SetValue(90)
        self.progress_bar.SetValue(100)

        self.tool_bar()

        panel = MyPanel(self, self.q, self.q.path)

        self.sizer.Add(panel)
        self.sizer.Layout()

    def on_close(self, event):
        self.Destroy()

    def on_choose_file(self, event):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            self.path = str(self.dirname + '//' + self.filename)

            self.progress_bar.Show()
            self.progress_bar.SetValue(10)
            self.progress_bar.Pulse()

            self.statusbar.SetStatusText("Downloading...", 0)
        dlg.Destroy()
        try:
            self.flag = "qar"
            self.q = WorkerThread(self, self.path, self.flag)
        except:
            pass

    def on_choose_cf(self, event):  # choose compact flash
        # In this case we include a "New directory" button.
        dlg = wx.DirDialog(self, "Choose a directory:",
                          style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
        # Only destroy a dialog after you're done with it.
        dlg.Destroy()
        try:
            self.flag = "cf"
            self.q = WorkerThread(self, self.path, self.flag)
        except:
            pass

    def save(self, event):

        separator = self.selected.find(':')

        start = int(self.selected[:separator])
        end = int(self.selected[separator + 1:])

        self.get_path_to_save()

        self.progress_bar.Show()
        self.progress_bar.SetValue(5)
        self.progress_bar.Pulse()

        name = self.form_name("flight")
        f = Flight(self.progress_bar, start, end, self.q.path, name, self.qar_type,
                   self.path_to_save, self.flag)
        self.progress_bar.SetValue(100)

    def save_raw(self, event):
        separator = self.selected.find(':')

        start = int(self.selected[:separator])
        end = int(self.selected[separator + 1:])

        self.get_path_to_save()

        self.progress_bar.Show()
        self.progress_bar.SetValue(5)
        self.progress_bar.Pulse()

        name = self.form_name("raw")
        f = Flight(self.progress_bar, start, end, self.q.path, name, self.qar_type,
                   self.path_to_save, self.flag)
        self.progress_bar.SetValue(100)

    def form_name(self, rec_type):
        if rec_type == "flight":
            date = datetime.datetime.now()
            name = "flight_" + date.strftime("%H%M%S_%d%m%y")
            self.statusbar.SetStatusText("Flight is exported", 0)
            return name
        elif rec_type == "raw":
            date = datetime.datetime.now()
            name = "raw_" + date.strftime("%H%M%S_%d%m%y")
            self.statusbar.SetStatusText("Raw file is exported", 0)
            return name

    def get_path_to_save(self):
        save_dialog = wx.DirDialog(self, "Choose a directory to save file:",
                                   style=wx.DD_DEFAULT_STYLE
                                   #| wx.DD_DIR_MUST_EXIST
                                   #| wx.DD_CHANGE_DIR
                                   )
        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it.
        if save_dialog.ShowModal() == wx.ID_OK:
            self.path_to_save = save_dialog.GetPath()

#----------------------------------------------------------------------

app = wx.App(False)
frame = MyFrame()
app.MainLoop()

