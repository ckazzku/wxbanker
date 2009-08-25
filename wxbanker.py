#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    wxbanker.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.

import os

# wxPython
try:
    import wxversion
except ImportError:
    # Maybe we don't have wxversion but still have wx >= 2.8?
    import wx, wx.aui
else:
    # Okay, let's try to get >= 2.8
    wxversion.ensureMinimal("2.8")
    import wx, wx.aui

from wx.lib.pubsub import Publisher

# wxBanker
from bankexceptions import NoNumpyException
from menubar import BankMenuBar
import localization, messagepanel
# Tabs
import managetab
try:
    import summarytab
except NoNumpyException:
    summarytab = None
    print _("Warning: Numpy module not available, disabling Summary tab. Install numpy to fix this.")


class BankerPanel(wx.Panel):
    def __init__(self, parent, bankController):
        wx.Panel.__init__(self, parent)
        self.bankController = bankController

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = notebook = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP)

        self.managePanel = managetab.ManagePanel(notebook, bankController)
        notebook.AddPage(self.managePanel, _("Transactions"))

        if summarytab:
            self.summaryPanel = summarytab.SummaryPanel(notebook, bankController)
            notebook.AddPage(self.summaryPanel, _("Summary"))
            
        self.Sizer.Add(self.notebook, 1, wx.EXPAND)

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.onTabSwitching)
        Publisher.subscribe(self.onRecurringTransactionAdded, "recurringtransaction.created")
        
        wx.CallLater(1000, self.CheckRecurringTransactions)
        
    def AddMessagePanel(self, panel):
        self.Sizer.Insert(0, panel, 0, wx.EXPAND)
        self.Layout()

    def CheckRecurringTransactions(self):
        recurring = self.bankController.Model.GetRecurringTransactions()
        message = _("%(num)i recurring transactions are due to occur")  % {"num": len(dates)}
        mpanel = messagepanel.MessagePanel(self, message)
        self.AddMessagePanel(mpanel)
        
        return len(recurring)
    
    def onRecurringTransactionAdded(self, message):
        account, recurring = message.data
        dates = recurring.GetUntransactedDates()
        
        # If there are transactions due, inform the user via the normal route.
        if dates:
            self.CheckRecurringTransactions()
        # Otherwise, just inform the user it was added, and the first date.
        else:
            message = _("Recurring transaction successfully added.")
            futureDates = recurring.GetUntransactedDates(future=True)
            if futureDates:
                message += _("The first transaction will occur on %(date)s") % {"date": futureDates[0]}
            mpanel = messagepanel.MessagePanel(self, message)
            self.AddMessagePanel(mpanel)

    def onTabSwitching(self, event):
        tabIndex = event.Selection
        # If we are switching to the summary (graph) tab, update it!
        if tabIndex == 1:
            self.summaryPanel.update()
        
        
class BankerFrame(wx.Frame):
    def __init__(self, bankController, welcome):
        # Load our window settings.
        config = wx.Config.Get()
        size = config.ReadInt('SIZE_X'), config.ReadInt('SIZE_Y')
        pos = config.ReadInt('POS_X'), config.ReadInt('POS_Y')

        wx.Frame.__init__(self, None, title="wxBanker", size=size, pos=pos)
        self.SetIcon(wx.ArtProvider.GetIcon('wxART_coins'))

        self.Panel = BankerPanel(self, bankController)
        
        Publisher.subscribe(self.onWarning, "warning")
        if welcome:
            Publisher.subscribe(self.onFirstRun, "first run")

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        menuBar = BankMenuBar(bankController.AutoSave)
        self.SetMenuBar(menuBar)
        #self.CreateStatusBar()

        self.Bind(wx.EVT_MENU, menuBar.onMenuEvent)

    def OnMove(self, event):
        config = wx.Config.Get()

        x, y = self.GetPosition()
        config.WriteInt("POS_X", x)
        config.WriteInt("POS_Y", y)

        event.Skip()

    def OnSize(self, event):
        config = wx.Config.Get()

        if not self.IsMaximized():
            x, y = self.GetSize()
            config.WriteInt('SIZE_X', x)
            config.WriteInt('SIZE_Y', y)

        config.WriteBool('IsMaximized', self.IsMaximized())
        event.Skip()

    def OnClose(self, event):
        event.Skip() # This must be first, so handlers can override it.
        Publisher.sendMessage("exiting", event)

    def onFirstRun(self, message):
        welcomeMsg = _("It looks like this is your first time using wxBanker!")
        welcomeMsg += "\n\n" + _("To get started, add an account using the account control in the top left corner.")
        welcomeMsg += " " + _("The buttons in the account control allow you to add, remove, and rename an account, respectively.")
        welcomeMsg += "\n\n" + _("Once you have created an account you can add transactions to it (such as your initial balance) using the controls below the grid on the bottom right.")
        welcomeMsg += "\n\n" + _("Have fun!")
        #wx.TipWindow(self, welcomeMsg, maxLength=300)
        dlg = wx.MessageDialog(self, welcomeMsg, _("Welcome!"), style=wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onWarning(self, message):
        warning = message.topic[1]
        if warning == "dirty exit":
            event = message.data
            title = _("Save changes?")
            msg = _("You have made changes since the last save. Would you like to save before exiting?")
            msg += "\n\n" + _("Note that enabling auto-save from the File menu will eliminate the need for manual saving.")
            dlg = wx.MessageDialog(self, msg, title, style=wx.CANCEL|wx.YES_NO|wx.ICON_WARNING)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                Publisher.sendMessage("user.saved")
            elif result == wx.ID_CANCEL:
                # The user cancelled the close, so cancel the event skip.
                event.Skip(False)
            dlg.Destroy()


def init(path=None, welcome=True):
    import wx, os, sys, fileservice
    
    from controller import Controller

    bankController = Controller(path)

    if '--cli' in sys.argv:
        import clibanker
        clibanker.main(bankController)
    else:
        # Push our custom art provider.
        import wx.lib.art.img2pyartprov as img2pyartprov
        from art import silk
        wx.ArtProvider.Push(img2pyartprov.Img2PyArtProvider(silk))

        # Initialize the wxBanker frame!
        frame = BankerFrame(bankController, welcome)

        # Greet the user if it appears this is their first time using wxBanker.
        config = wx.Config.Get()
        firstTime = not config.ReadBool("RUN_BEFORE")
        if firstTime:
            Publisher().sendMessage("first run")
            config.WriteBool("RUN_BEFORE", True)

        return bankController.wxApp


def main():
    app = init()
    app.TopWindow.Show()

    import sys
    if '--inspect' in sys.argv:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()


if __name__ == "__main__":
    main()
