#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    bankmodel.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import wx
from wx.lib.pubsub import Publisher
import wx.lib.delayedresult as delayedresult
import re, datetime

from wxbanker import currencies
from wxbanker.bankobjects.ormobject import ORMKeyValueObject
from wxbanker.bankobjects.accountlist import AccountList
from wxbanker.mint.api import Mint

from wxbanker.currencies import GetCurrencyInt

class BankModel(ORMKeyValueObject):
    ORM_TABLE = "meta"
    ORM_ATTRIBUTES = ["LastAccountId", "MintEnabled", "GlobalCurrency"]
    
    def __init__(self, store):
        ORMKeyValueObject.__init__(self, store)
        self.Store = store
        self.Accounts = AccountList(self, store)
        self._Tags = {}

        # Handle Mint integration, but send the message in the main thread, otherwise, dead.
        if self.MintEnabled:
            delayedresult.startWorker(lambda result: Publisher.sendMessage("mint.updated"), Mint.LoginFromKeyring, wkwargs={"notify": False})

        Publisher.subscribe(self.onGlobalCurrencyChanged, "user.global_currency_changed")
        Publisher.subscribe(self.onAccountCurrencyChanged, "user.account_currency_changed")
        Publisher.subscribe(self.onMintToggled, "user.mint.toggled")
        Publisher.subscribe(self.onAccountChanged, "view.account changed")
        Publisher.subscribe(self.onTransactionTagged, "transaction.tagged")
        Publisher.subscribe(self.onTransactionUntagged, "transaction.untagged")
        
    def GetLastAccount(self):
        return self.Accounts.GetById(self.LastAccountId)

    def GetBalance(self):
        return self.Accounts.Balance
    
    def GetRecurringTransactions(self):
        return self.Accounts.GetRecurringTransactions()

    def GetTransactions(self):
        transactions = []
        for account in self.Accounts:
            transactions.extend(account.Transactions)

        return transactions
    
    def GetDateRange(self):
        """Get the date of the first and last transaction."""
        transactions = self.GetTransactions()
        
        # If there are no transactions, let's go with today.
        if not transactions:
            return datetime.date.today(), datetime.date.today()
        else:
            # Sorting transactions is very important, otherwise the first and last dates are arbitrary!
            transactions.sort()
            return transactions[0].Date, transactions[-1].Date

    def GetXTotals(self, account=None, daterange=None):
        """
        Get totals every so many days, optionally within a specific account
        and/or date range. This is particularly useful when we want to
        graph a summary of account balances.
        """
        if account is None:
            transactions = self.GetTransactions()
            currency = self.GlobalCurrency
        else:
            transactions = account.Transactions[:]
            currency = GetCurrencyInt(account.GetCurrency())
        transactions.sort()
        
        if transactions == []:
            return []
        
        startingBalance = 0.0
        # Crop transactions around the date range, if supplied.
        if daterange:
            startDate, endDate = daterange
            starti, endi = None, len(transactions)
            total = 0.0
            for i, t in enumerate(transactions):
                if starti is None and t.Date >= startDate:
                    starti = i
                    startingBalance = total
                if t.Date > endDate:
                    endi = i
                    break
                total += t.GetAmount(currency)
                
            transactions = transactions[starti:endi]
        else:
            # Figure out the actual start and end dates we end up with.
            startDate, endDate = transactions[0].Date, transactions[-1].Date
        
        # If the last transaction was before today, we still want to graph until today.
        today = datetime.date.today()
        if daterange:
            endDate = daterange[1]
        elif today > endDate:
            endDate = today
       
        onedaydelta = datetime.timedelta(days=1)
        # Generate day totals
        totals = []
        currDate = startDate
        tindex = 0
        balance = startingBalance
        while currDate <= endDate:
            while tindex < len(transactions) and transactions[tindex].Date <= currDate:
                balance += transactions[tindex].GetAmount(currency)
                tindex += 1
            totals.append([currDate, balance])
            currDate += onedaydelta

        return totals

    def CreateAccount(self, accountName):
        return self.Accounts.Create(accountName)

    def RemoveAccount(self, accountName):
        return self.Accounts.Remove(accountName)

    def Search(self, searchString, account=None, matchIndex=1):
        """
        matchIndex: 0: Amount, 1: Description, 2: Date
        I originally used strings here but passing around and then validating on translated
        strings seems like a bad and fragile idea.
        """
        # Handle account options.
        if account is None:
            potentials = self.GetTransactions()
        else:
            potentials = account.Transactions[:]

        # Find all the matches.
        matches = []
        for trans in potentials:
            potentialStr = unicode((trans.Amount, trans.Description, trans.Date)[matchIndex])
            if re.findall(searchString, potentialStr, flags=re.IGNORECASE):
                matches.append(trans)
        return matches

    def Save(self):
        self.Store.Save()

    def float2str(self, *args, **kwargs):
        """
        Handle representing floats as strings for non
        account-specific amounts, such as totals.
        """
        currency = currencies.CurrencyList[self.GlobalCurrency]()
        return currency.float2str(*args, **kwargs)

    def setGlobalCurrency(self, currencyIndex):
        self.Store.setCurrency(currencyIndex)
        Publisher.sendMessage("currency_changed", currencyIndex)

    def setAccountCurrency(self, account, currencyIndex):
        self.Store.setCurrency(currencyIndex, account)
        account.SetCurrency(currencyIndex)
        Publisher.sendMessage("currency_changed", currencyIndex)
    
    def onGlobalCurrencyChanged(self, message):
        currencyIndex = message.data
        self.setGlobalCurrency(currencyIndex)
    
    def onAccountCurrencyChanged(self, message):
        account, currency = message.data
        self.setAccountCurrency(account, currency)
    
    def onAccountChanged(self, message):
        account = message.data
        if account:
            self.LastAccountId = account.ID
        else:
            self.LastAccountId = None
            
    def onTransactionTagged(self, message):
        tagNames = message.data
        for tag in tagNames:
            if tag in self._Tags:
                self._Tags[tag] += 1
            else:
                self._Tags[tag] = 1
                
    def onTransactionUntagged(self, message):
        tagNames = message.data
        for tag in tagNames:
            self._Tags[tag] -= 1
            if self._Tags[tag] == 0:
                self._Tags.pop(tag)
                
    def onMintToggled(self, message):
        enabled = message.data
        self.MintEnabled = enabled

    def __eq__(self, other):
        return (
            self.Accounts == other.Accounts and
            self.Tags == other.Tags and
            self.MintEnabled == other.MintEnabled 
        )

    def Print(self):
        print "Model: %s" % self.Balance
        for a in self.Accounts:
            print "  %s: %s" % (a.Name, a.Balance)
            for t in a.Transactions:
                print t
                
    def GetTags(self):
        return set(self._Tags.keys())

    Balance = property(GetBalance)
    Tags = property(GetTags)
