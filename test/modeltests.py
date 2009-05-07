#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    modeltests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import sys; sys.path.append("../")
import os, controller, unittest
from wx.lib.pubsub import Publisher

class ModelTests(unittest.TestCase):
    def setUp(self):
        Publisher.unsubAll()
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
            
        self.Controller = controller.Controller("test.db")
        self.Model = self.Controller.Model
        
    def testControllerIsAutoSavingByDefault(self):
        self.assertTrue( self.Controller.AutoSave )
    
    def testNewAccountIsSameCurrencyAsOthers(self):
        # This test is only valid so long as only one currency is allowed.
        # Otherwise it needs to test a new account gets the right default currency, probably Localized
        import currencies
        model = self.Controller.Model
        
        account = model.CreateAccount("Hello")
        self.assertEqual(account.Currency, currencies.LocalizedCurrency())
        
        account.Currency = currencies.EuroCurrency()
        self.assertEqual(account.Currency, currencies.EuroCurrency())
        
        account2 = model.CreateAccount("Another!")
        self.assertEqual(account2.Currency, currencies.EuroCurrency())
        
    def testBlankModelsAreEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model2)
    
    def testAutoSaveDisabledSimple(self):
        self.Controller.AutoSave = False
        self.assertFalse( self.Controller.AutoSave )
        
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")
        
        model2 = self.Controller.LoadPath("test.db")

        self.assertNotEqual(model1, model2)
        
    def testLoadingTransactionsPreservesReferences(self):
        a = self.Model.CreateAccount("A")
        t = a.AddTransaction(1, "First")
        self.assertEqual(t.Description, "First")
        
        # When we do a.Transactions, the list gets loaded with new
        # transaction objects, so let's see if the containership test works.
        self.assertTrue(t in a.Transactions)
        
        # 't' is the original transaction object created before Transactions
        # was loaded, but it should be in the list due to magic.
        t.Description = "Second"
        self.assertEqual(a.Transactions[0].Description, "Second")
        
    def testAutoSaveDisabledComplex(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")
        t1 = a1.AddTransaction(-10, "Description 1")

        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model2)
        self.Controller.Close(model2)
        
        self.Controller.AutoSave = False
        t2 = a1.AddTransaction(-10, "Description 3")
        model3 = self.Controller.LoadPath("test.db")
        self.assertFalse(model1 is model3)
        self.assertNotEqual(model1, model3)
        self.Controller.Close(model3)
        
        model1.Save()
        model4 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model4)
        self.Controller.Close(model4)
        
        t1.Description = "Description 2"
        model5 = self.Controller.LoadPath("test.db")
        self.assertNotEqual(model1, model5)
        
        model1.Save()
        model6 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model6)
        
    def testEnablingAutoSaveSaves(self):
        self.Controller.AutoSave = False
        self.Model.CreateAccount("A")
        
        # The model has unsaved changes, a new one should be different.
        model2 = self.Controller.LoadPath("test.db")
        self.assertNotEqual(self.Model, model2)
        self.Controller.Close(model2)
        
        # Setting AutoSave to true should trigger a save.
        self.Controller.AutoSave = True
        
        # Now a newly loaded should be equal.
        model3 = self.Controller.LoadPath("test.db")
        self.assertEqual(self.Model, model3)
        self.Controller.Close(model3)
        
        
    def testSimpleMove(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)
        
        b = model1.CreateAccount("B")
        
        a.MoveTransaction(t1, b)
        
        self.assertFalse(t1 in a.Transactions)
        self.assertTrue(t1 in b.Transactions)
        self.assertNotEqual(t1.Parent, a)
        self.assertEqual(t1.Parent, b)
        
    def testTransactionPropertyBug(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)
        self.assertEqual(len(a.Transactions), 1)
        
    def testSaveEventSaves(self):
        self.Controller.AutoSave = False
        model1 = self.Controller.Model
        
        # Create an account, don't save.
        self.assertEqual(len(model1.Accounts), 0)
        model1.CreateAccount("Hello!")
        self.assertEqual(len(model1.Accounts), 1)
        
        # Make sure that account doesn't exist on a new model
        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(len(model2.Accounts), 0)
        self.assertNotEqual(model1, model2)
        
        # Save
        Publisher.sendMessage("user.saved")
        
        # Make sure it DOES exist after saving.
        model3 = self.Controller.LoadPath("test.db")
        self.assertEqual(len(model3.Accounts), 1)
        self.assertEqual(model1, model3)
        self.assertNotEqual(model2, model3)
        
    def testRenameIsStored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        a.Name = "B"
        
        model2 = model1.Store.GetModel()
        self.assertEqual(model1, model2)
        
    def testBalanceIsStored(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("A")
        self.assertEqual(a1.Balance, 0)
        
        a1.AddTransaction(1)
        self.assertEqual(a1.Balance, 1)
        
        model2 = model1.Store.GetModel()
        a2 = model2.Accounts[0]
        self.assertEqual(model1, model2)
        self.assertEqual(a1.Balance, a2.Balance)
        
    def testTransactionChangeIsStored(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("A")

        t1 = a1.AddTransaction(-1.25)
        
        t1.Description = "new"
        t1.Amount = -1.50
        
        model2 = model1.Store.GetModel()
        self.assertEqual(model1, model2)
        
    def testDirtyExitWarns(self):
        """
        This test is kind of hilarious. We want to make sure we are warned of
        exiting with a dirty model, so we create an account, register a callback
        which will change its name when the dirty warning goes out, then trigger
        a dirty exit and make sure the account name has changed.
        """
        self.Controller.AutoSave = False
        a = self.Model.CreateAccount("Unwarned!")

        # Create and register our callback to test for the warning message.
        def cb(message):
            a.Name = "Warned"
        Publisher.subscribe(cb, "warning.dirty exit")
            
        # Now send the exiting message, which should cause our callback to fire if everything is well.
        Publisher.sendMessage("exiting")
        
        self.assertEqual(a.Name, "Warned")
        
    def tearDown(self):
        self.Controller.Close()
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)