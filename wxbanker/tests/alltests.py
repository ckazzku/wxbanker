#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    alltests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker.tests import testbase, xmlrunner
import unittest, os, sys

# Find the modules to test.
ignores = ('__init__.py', 'testbase.py', 'alltests.py', 'xmlrunner.py')
files = [f for f in os.listdir(testbase.testdir) if f.endswith(".py") and f not in ignores]
modules = [m.replace(".py", "") for m in files]

def main():
    as_xml = "--xml" in sys.argv
    if as_xml:
        runner = xmlrunner.XMLTestRunner(filename="pyunit.xml")
    else:
        runner = unittest.TextTestRunner()

    suite = unittest.TestLoader().loadTestsFromNames(modules)
    result = runner.run(suite)

    incomplete = testbase.INCOMPLETE_TESTS
    if incomplete:
        print "Incomplete tests: %i!" % incomplete

    if not (as_xml or result.wasSuccessful()):
        sys.exit(1)

if __name__ == "__main__":
    main()
