# This file is part of gtkPacman.
#
# gtkPacman is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# gtkPacman is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gtkPacman; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# gtkPacman is copyright (C)2005-2008 by Stefano Esposito

from vte import Terminal

class terminal(Terminal):

    def __init__(self):

        Terminal.__init__(self)
        self.set_sensitive(False)

    def do(self, queues):
        names_queues = { "add": [], "remove": []}

        for pac in queues["add"]:
            names_queues["add"].append(pac.name)
            continue
        for pac in queues["remove"]:
            names_queues["remove"].append(pac.name)
            continue

        inst_pacs = " ".join(names_queues["add"])
        rem_pacs = " ".join(names_queues["remove"])

        pacman = "pacman --noconfirm"
        
        if inst_pacs and rem_pacs:
            command = "%s -Sdf %s;%s -Rdf %s;exit\n" %(pacman, inst_pacs, pacman, rem_pacs)

        elif inst_pacs:
            command = "%s -Sdf %s;exit\n" %(pacman, inst_pacs)

        elif rem_pacs:
            command = "%s -Rdf %s;exit\n" %(pacman, rem_pacs)

        else:
            command = "exit\n"
            
        self.fork_command()
        self.feed_child(command)

    def do_local(self, fname, queues):
        names_queues = { "add": [], "remove": []}
        
        for pac in queues["add"]:
            names_queues["add"].append(pac.name)
            continue
        for pac in queues["remove"]:
            names_queues["remove"].append(pac.name)
            continue

        inst_pacs = " ".join(names_queues["add"])
        rem_pacs = " ".join(names_queues["remove"])

        pacman = "pacman --noconfirm"
        local = "%s -Uf %s" %(pacman, fname)

        if inst_pacs and rem_pacs:
            command = "%(pac)s -Sdf %(inst)s;%(pac)s -Rdf %(rem)s;%(loc)s;exit\n" %{"pac": pacman, "loc": local, "inst": inst_pacs, "rem": rem_pacs}
        elif inst_pacs:
            command = "%(pac)s -Sdf %(inst)s;%(pac)s;%(loc)s;exit\n" %{"pac": pacman, "loc": local, "inst": inst_pacs}
        elif rem_pacs:
            command = "%(loc)s;%(pac)s -Rdf %(rem)s;%(loc)s;exit\n" %{"pac": pacman, "loc": local, "rem": rem_pacs}
        else:
            command = "%s;exit\n" %local

        self.fork_command()
        self.feed_child(command)

    def do_upgrade(self):
        self.fork_command()
        self.feed_child("pacman -Su --noconfirm;exit\n")

    def close(self, term, close_button):
        close_button.show()
        return
