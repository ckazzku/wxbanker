import wx
from csvimporter import CsvImporter, CsvImporterSettings
from banker import Bank

class CsvImportFrame(wx.Frame):
    """
    Window for importing data from a CSV file
    """
    def __init__(self):
        wx.Frame.__init__(self, None, title=_("CSV import"))
        
        topPanel = wx.Panel(self)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        
        # target Account
        staticBox = wx.StaticBox(topPanel, label=_("Target account"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)

        try:
            accounts = Bank().getAccountNames()
        except:
            accounts = []
        
        self.targetAccountCtrl = wx.ComboBox(topPanel, style=wx.CB_READONLY, choices=accounts)
        self.targetAccountCtrl.Bind(wx.EVT_COMBOBOX, self.onTargetAccountChange)
        staticBoxSizer.Add(self.targetAccountCtrl)
        
        # csv columns to wxBanker data mapping
        
        staticBox = wx.StaticBox(topPanel, label=_("CSV columns mapping"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)
        
        sizer = wx.FlexGridSizer(rows=3, cols=4, hgap=15, vgap=0)
        sizer.SetFlexibleDirection(wx.HORIZONTAL)
        staticBoxSizer.Add(sizer, flag=wx.ALL|wx.EXPAND, border=5)
        
        self.dateColumnCtrl = wx.TextCtrl(topPanel, size=(30,-1), value='1')
        sizer.Add(wx.StaticText(topPanel, label=_('Date')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.dateColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        dateFormats = ['%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        self.dateFormatCtrl = wx.ComboBox(topPanel, value=dateFormats[0], choices=dateFormats, size=(110,-1))
        sizer.Add(wx.StaticText(topPanel, label=_('Date format')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.dateFormatCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.amountColumnCtrl = wx.TextCtrl(topPanel, size=(30,-1), value='2')
        self.decimalSeparatorCtrl = wx.TextCtrl(topPanel, size=(20,-1), value='.')
        sizer.Add(wx.StaticText(topPanel, label=_('Amount')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.amountColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(wx.StaticText(topPanel, label=_('Decimal separator')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.decimalSeparatorCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        self.descriptionColumnCtrl = wx.TextCtrl(topPanel, value='3 4 5')
        sizer.Add(wx.StaticText(topPanel, label=_('Description')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.descriptionColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add((0,0))
        sizer.Add((0,0))
        
        # csv file settings - delimiter, encoding, first line has headers - skipped
        
        staticBox = wx.StaticBox(topPanel, label=_("CSV file settings"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)
        
        sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=15, vgap=0)
        sizer.SetFlexibleDirection(wx.HORIZONTAL)
        staticBoxSizer.Add(sizer);
        
        self.skipFirstLineCtrl = wx.CheckBox(topPanel)
        sizer.Add(wx.StaticText(topPanel, label=_('Skip first line')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.skipFirstLineCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(wx.StaticText(topPanel, label=_('Encoding')), flag=wx.ALIGN_CENTER_VERTICAL)
        encodings = ['cp1250', 'utf-8']
        self.fileEncodingCtrl = wx.ComboBox(topPanel, value='utf-8', choices=encodings, size=(110,-1))
        sizer.Add(self.fileEncodingCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        sizer.Add(wx.StaticText(topPanel, label=_('Column delimiter')), flag=wx.ALIGN_CENTER_VERTICAL)
        self.delimiterCtrl = wx.TextCtrl(topPanel, value=';', size=(30,-1),)
        sizer.Add(self.delimiterCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        
        # file picker control and import button
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(sizer, flag=wx.EXPAND|wx.ALL, border=5)
        
        sizer.Add(wx.StaticText(topPanel, label=_('File to import')), flag=wx.ALIGN_CENTER_VERTICAL)
        self.filePickerCtrl = wx.FilePickerCtrl(topPanel)
        self.filePickerCtrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.onFileChange)
        sizer.Add(self.filePickerCtrl, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, proportion=2, border=10)
		
        self.importButton = wx.Button(topPanel, label=_("Import"))
        self.importButton.Disable()
        self.importButton.SetToolTipString(_("Import"))
        self.importButton.Bind(wx.EVT_BUTTON, self.onClickImportButton)
        sizer.Add(self.importButton)

        # layout sizers
        topPanel.SetSizer(topSizer)
        topPanel.SetAutoLayout(True)
        topSizer.Fit(self)
        
        self.Show(True)
    
    def runImport(self):
        importer = CsvImporter()
        settings = CsvImporterSettings()

        settings.amountColumn = int(self.amountColumnCtrl.Value) - 1
        settings.decimalSeparator = self.decimalSeparatorCtrl.Value
        
        settings.dateColumn = int(self.dateColumnCtrl.Value) - 1
        settings.dateFormat = self.dateFormatCtrl.Value

        settings.descriptionColumns = [int(col) - 1 for col in self.descriptionColumnCtrl.Value.split()]

        settings.delimiter = str(self.delimiterCtrl.Value)
        settings.skipFirstLine = self.skipFirstLineCtrl.Value
        settings.encoding = self.fileEncodingCtrl.Value
        
        file = self.filePickerCtrl.Path
        
        try:
            importer.importFile('Sporitelna', file, settings)
        except Exception, e:
            print 'Caught exception:', e
        
    def onFileChange(self, event):
        if self.targetAccountCtrl.Value != '':
            self.importButton.Enable()
            
    def onTargetAccountChange(self, event):
        if self.filePickerCtrl.Path != '':
            self.importButton.Enable()

    def onClickImportButton(self, event):
        self.runImport()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = CsvImportFrame()
    app.MainLoop()
