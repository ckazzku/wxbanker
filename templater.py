#!/usr/bin/env python
#    https://launchpad.net/wxbanker
#    templater.py: Copyright 2007, 2008 Mike Rooney <mrooney@ubuntu.com>
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

import os, commands, shutil, pprint, tarfile

"""
Some strings are displayed dynamically, and so we need to "hard code"
the possibilities here so they get in the templates and translated.
"""
_ = lambda s: s
_("Hide Calculator")
_("Show Calculator")
_("Transact") # Keep this here for now, might want it.


def gentemplate(name="wxbanker.pot"):
    """Generate a .pot template with the given name."""
    translatableFiles = [f for f in os.listdir(".") if f.endswith(".py")]
    command = "xgettext %s" % " ".join(translatableFiles) + " --output=po/%s"%name
    print commands.getstatusoutput(command)
    
def export2import(tarOrExtracted):
    """Launchpad does not support importing exported po files without some massage."""
    try:
        isTar = tarfile.is_tarfile(tarOrExtracted)
    except Exception:
        isTar = False
        
    if isTar:
        tar = tarfile.open(tarOrExtracted)
        tar.extractall("tmp")
        exportDir = "tmp"
    elif os.path.isdir(tarOrExtracted):
        exportDir = tarOrExtracted
    else:
        raise Exception("Must pass location of either tar.gz file or extracted directory")
        
    os.chdir(exportDir)

    def nameto(po, d):
        """Rename the .po file appropriately and move it to where it belongs."""
        print "naming %s..." % po
        locale = po[po.find("-")+1:-3]
        newname = "%s.po" % locale
        os.rename(po, newname)
        shutil.move(newname, d)
    
    for x in os.listdir("po"):
        path = os.path.join("po", x)
        if x.endswith(".po"):
            nameto(path, "po/")
        else:
            os.remove(path)
    
    for item in os.listdir("."):
        if os.path.isdir(item):
            if item != "po":
                # Sometimes there are more .po files in a domain directory.
                # These need to be named and moved to ../po/
                os.chdir(item)
                for po in (f for f in os.listdir(".") if f.endswith(".po")):
                    nameto(po, "../po/")
                os.chdir("../")
                os.rmdir(item)
        elif item.endswith(".po"):
            # Name it properly and move it to po/
            nameto(item, "po/")
        
    #tarfile.open("massaged.tar.gz", "w|gz")

if __name__ == "__main__":
    import sys
    if sys.argv[1] == "-lp":
        export2import(sys.argv[2])
    else:
        gentemplate()
