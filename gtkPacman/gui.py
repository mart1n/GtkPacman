# This file is part of gtkPacman.

# gtkPacman is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# gtkPacman is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with gtkPacman; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# gtkPacman is copyright (C)2005-2008 by Stefano Esposito

import gettext, gobject

from gtk import main, main_quit, TreeStore, TreeView, ListStore, Button
from gtk import CellRendererText, CellRendererPixbuf, ScrolledWindow
from gtk import STOCK_ADD, STOCK_GO_UP, STOCK_REMOVE, STOCK_CLOSE
from gtk import RESPONSE_YES, RESPONSE_ACCEPT, RESPONSE_OK, RESPONSE_NO
from gtk.gdk import pixbuf_new_from_file, Cursor, WATCH
from gtk.glade import XML

from dialogs import non_root_dialog, about_dialog, warning_dialog, do_dialog 
from dialogs import confirm_dialog, search_dialog, upgrade_dialog
from dialogs import upgrade_confirm_dialog, local_install_dialog
from dialogs import local_install_fchooser_dialog, local_confirm_dialog
from dialogs import command_dialog, error_dialog, ignorepkg_dialog
from dialogs import holdpkg_dialog, choose_pkgbuild_dialog, change_user_dialog

from models import installed_list, all_list, whole_list, search_list, file_list

class gui:
    def __init__(self, fname, database, uid, icon):

        # Setup the main gui: read glade file, connect signals
        self.gld = XML(fname, "main_win", "gtkpacman")
        self.gld.get_widget("main_win").set_icon(pixbuf_new_from_file(icon))

        h_dict = {"quit":           self.quit,
                  "add_install":    self.add_to_install_queue,
                  "remove_install": self.remove_from_install_queue,
                  "add_remove":     self.add_to_remove_queue,
                  "remove_remove":  self.remove_from_remove_queue,
                  "execute":        self.execute,
                  "up_sys":         self.upgrade_system,
                  "refr_db":        self.refresh_database,
                  "add_local":      self.add_from_local_file,
                  "clear_cache":    self.clear_cache,
                  "empty_cache":    self.empty_cache,
                  "search_pac":     self.search,
                  "show_popup":     self.show_popup,
                  "about":          self.about,
                  "pacs_changed":   self.pacs_changed,
                  "repo_changed":   self.repo_changed,
                  "make_pkg":       self.make_package}
        self.gld.signal_autoconnect(h_dict)


        self.fname = fname
        self.icon = icon
        self.database = database
        self.queues = {"add": [], "remove": []}
        self.search_iter = None

        #Setup secondary gui elements
        self._setup_popup_menu(fname)
        self._setup_repos_tree()
        self._setup_pacs_models()
        self._setup_pacs_tree()
        self._setup_files_tree()

        #Setup statusbar
	self._statusbar()

        #Check if root, else notufy it and deactivate some widgets
        if uid:
            self._setup_avaible_actions()
            dlg = non_root_dialog(icon)
            dlg.run()
            dlg.destroy()

    def _setup_avaible_actions(self):
        #Deactivate some widgets. Called if not root
        self.gld.get_widget("queue").set_sensitive(False)
        self.gld.get_widget("immediate").set_sensitive(False)
        self.gld.get_widget("add_install").set_sensitive(False)
        self.gld.get_widget("remove_install").set_sensitive(False)
        self.gld.get_widget("add_remove").set_sensitive(False)
        self.gld.get_widget("remove_remove").set_sensitive(False)
        self.gld.get_widget("execute").set_sensitive(False)
        self.gld.get_widget("up_sys").set_sensitive(False)
        self.gld.get_widget("up_db").set_sensitive(False)
        
        self.popup_gld.get_widget("popup_add_install").set_sensitive(False)
        self.popup_gld.get_widget("popup_remove_install").set_sensitive(False)
        self.popup_gld.get_widget("popup_add_remove").set_sensitive(False)
        self.popup_gld.get_widget("popup_remove_remove").set_sensitive(False)
    
    def _adjust_queues (self):
        for name in self.queues["add"]:
            if name == "x-server":
                ind = self.queues["add"].index("x-server")
                self.queues["add"][ind] = "x-org"
            elif ">=" in name:
                ind = self.queues["add"].index(name)
                name = name.split(">=")[0]
                self.queues["add"][ind] = name
            continue

    def _adjust_names(self, names):
        for ind in range(len(names)):
            if names[ind] == "x-server":
                names[ind] = "xorg-server"
            elif ">=" in names[ind]:
                name = names[ind].split(">=")[0]
                names[ind] = name
            continue
        return names
        
    def _setup_pacs_tree(self):
        pacs_tree = self.gld.get_widget("pacs_tree")

        pacs_tree.insert_column_with_attributes(-1, "", CellRendererPixbuf(),
                                                stock_id=0)
        pacs_tree.insert_column_with_attributes(-1, "", CellRendererPixbuf(),
                                                stock_id=1)
        pacs_tree.insert_column_with_attributes(-1, _("Package"),
                                                CellRendererText(), text=2)
        pacs_tree.insert_column_with_attributes(-1, _("Installed Version"),
                                                CellRendererText(), text=3)
        self.inst_ver_col = pacs_tree.insert_column_with_attributes(
            -1, _("Avaible Version"), CellRendererText(), text=4
            )
        self.repo_col = pacs_tree.insert_column_with_attributes(
            -1, _("Repo"),
            CellRendererText(), text=5
            )

        pacs_tree.set_model(self.models[_("All")])

        sort_id = 0
        for col in pacs_tree.get_columns():
            col.set_reorderable(True)
            col.set_sort_column_id(sort_id)
            col.set_clickable(True)
            col.set_resizable(True)
            sort_id += 1
            continue
        return

    def _setup_popup_menu(self, fname):
        self.popup_gld = XML(fname, "popup_menu", "gtkpacman")
        popup_h_dict = { "add_install": self.add_to_install_queue,
                         "remove_install": self.remove_from_install_queue,
                         "add_remove": self.add_to_remove_queue,
                         "remove_remove": self.remove_from_remove_queue,
                         "search": self.search }
        self.popup_gld.signal_autoconnect(popup_h_dict)
        self.popup = self.popup_gld.get_widget("popup_menu")

        
    def _setup_repos_tree(self):

        repos_tree = self.gld.get_widget("repos_tree")
                
        repos_tree.insert_column_with_attributes(-1, "", CellRendererText(),
                                                 text=0)
        repos_tree.set_model(self._make_repos_model())
        return

    def _make_repos_model (self):
        repos_model = TreeStore(str)
        all_it = repos_model.append(None, [_("All")])

        for repo in self.database.repos:
            if repo == "foreigners":
                continue
            repo_it = repos_model.append(all_it, [repo])
            repos_model.append(repo_it, [_("all")])
            repos_model.append(repo_it, [_("installed")])
            continue

        repos_model.append(all_it, [_("foreigners")])
        return repos_model
 
    def _pacs_tree_exp_check(self):
        expanded= []
        def expander_check(model, path, iter):
            is_expanded = repos_tree.row_expanded(path)
            if is_expanded:
                expanded.append(path)

        repos_tree = self.gld.get_widget("repos_tree")
        model = repos_tree.get_model()
        iter = model.get_iter_root()
        path = model.get_path(iter)
        model.foreach(expander_check)
        return expanded

    def _refresh_repos_tree (self):            
        expanded = self._pacs_tree_exp_check()
        
        repos_tree = self.gld.get_widget("repos_tree")
        repos_tree.set_model(self._make_repos_model())
        
        for row in expanded:
            repos_tree.expand_row(row, False)
        return
    
    def _setup_files_tree(self):

        file_tree = self.gld.get_widget("files")
        file_tree.insert_column_with_attributes(-1, "", CellRendererText(),
                                                text=0)
        return
        

    def _setup_pacs_models(self):
        self.models = {}

        self.models[_("All")] = whole_list(self.database.values())
        try:
            self.models[_("foreigners")] = installed_list(self.database["foreigners"])
        except KeyError:
            self.database["foreigners"] = []
            self.models[_("foreigners")] = installed_list(self.database["foreigners"])
            
        for repo in self.database.keys():
            if repo == _("foreigners"):
                continue
            
            self.models[repo] = {}

            all_mod = all_list(self.database[repo])
            inst_mod = installed_list(self.database[repo])

            self.models[repo][_("all")] = all_mod
            self.models[repo][_("installed")] = inst_mod
            continue
        return

    def _refresh_trees(self):
        for model in self.models.keys():
	    if model == _("All") or model == _("foreigners") or model == _("search"):
                self._refresh_model(model)
            else:
                try:
                    for mod in self.models[model].keys():
                        self._refresh_model(model, mod)
                        continue
                except AttributeError:
                    pass
            continue
        return

    def _refresh_model(self, model, submodel=None):
        if submodel:
            liststore = self.models[model][submodel]
        else:
            liststore = self.models[model]

        for row in liststore:
            row[1] = None
            check = row[2][:]
            if check in self.queues["remove"] and model ==  _("foreigners"):
                nr = 0
                for rm in liststore:
                    nr += 1
                    if check == rm[2]:
                        del liststore[nr -1]
            elif check in self.queues["remove"] and submodel ==  _("installed"):
                nr = 0
                for rm in liststore:
                    nr += 1
                    if check == rm[2]:
                        del liststore[nr -1]
            elif row[2] in self.queues["add"] and submodel =="all":
                row[0] = "green"
                row[3] = row[4]
                self.models[model]["installed"].append(row)
            elif row[2] in self.queues["add"]:
                row[0] = "green"
                row[3] = row[4]
            elif row[2] in self.queues["remove"]:
                row[0] = "red"
                row[3] = "-"
            continue
        return

    def quit(self, widget, data=None):
        main_quit()
        return

    def repo_changed(self, widget, data=None):
        repos_tree = self.gld.get_widget("repos_tree")
        pacs_tree = self.gld.get_widget("pacs_tree")
        
        repos_model, tree_iter = repos_tree.get_selection().get_selected()
        selected = repos_model.get_value(tree_iter, 0)

        if not repos_model.iter_depth(tree_iter):
            if selected.count(_("Search")):
                pacs_model = self.models["search"]
            else:
                pacs_model = self.models[_("All")]
            if not self.repo_col:
                self.repo_col = pacs_tree.insert_column_with_attributes(
                    -1, _("Repo"), CellRendererText(), text=5
                    )
            if not self.inst_ver_col:
                self.inst_ver_col = pacs_tree.insert_column_with_attributes(
                    -1, _("Available Version"), CellRendererText(), text=4
                    )
                
        elif selected == _("foreigners"):
            if self.repo_col:
                pacs_tree.remove_column(self.repo_col)
                self.repo_col = None
                
            if self.inst_ver_col:
                pacs_tree.remove_column(self.inst_ver_col)
                self.inst_ver_col = None
            
            pacs_model = self.models[selected]
            
        else:
            if selected == _("all") or selected == _("installed"):
                parent_iter = repos_model.iter_parent(tree_iter)
                parent = repos_model.get_value(parent_iter, 0)
                pacs_model = self.models[parent][selected]
            else:
                pacs_model = self.models[selected][_("all")]

            if self.repo_col:
                pacs_tree.remove_column(self.repo_col)
                self.repo_col = None
            if not self.inst_ver_col:
                self.inst_ver_col = pacs_tree.insert_column_with_attributes(
                    -1, _("Avaible Version"), CellRendererText(), text=4)
        pacs_tree.set_model(pacs_model)
	
	stat = (len(pacs_model), selected)
	self._statusbar(stat)

    def pacs_changed(self, widget, data=None):
        sum_txt = self.gld.get_widget("summary")
        sum_buf = sum_txt.get_buffer()

        file_tree = self.gld.get_widget("files")
               
        model, t_iter = widget.get_selection().get_selected()
        name = model.get_value(t_iter, 2)

        pac = self.database.get_by_name(name)
        if not pac.prop_setted:
            self.database.set_pac_properties(pac)

        sum_buf.set_text(pac.summary)

        file_model = file_list(pac.filelist)
        file_tree.set_model(file_model)
        return

    def add_to_install_queue(self, widget, data=None):
        tree = self.gld.get_widget("pacs_tree")
        model, l_iter = tree.get_selection().get_selected()
        
        try:
            name = model.get_value(l_iter, 2)
        except TypeError:
            return
        
        if name in self.queues["add"]:
            return
        
        image = model.get_value(l_iter, 0)
        
        if name in self.database.ignorePkg and image == 'green':
            dlg = ignorepkg_dialog(name, self.icon)
            res = dlg.run()
            dlg.destroy()
            if res == RESPONSE_NO:
                return
            
        if name in self.queues["remove"]:
            self.queues["remove"].remove(name)

        self.queues["add"].append(name)
        if image == "red":
            model.set_value(l_iter, 1, STOCK_ADD)
        else:
            model.set_value(l_iter, 1, STOCK_GO_UP)
        return

    def remove_from_install_queue(self, widget, data=None):
        tree = self.gld.get_widget("pacs_tree")
        model, l_iter = tree.get_selection().get_selected()

        try:
            name = model.get_value(l_iter, 2)
        except TypeError:
            return
        
        if not (name in self.queues["add"]):
            return

        self.queues["add"].remove(name)
        model.set_value(l_iter, 1, None)
        return

    def add_to_remove_queue(self, widget, data=None):
        tree = self.gld.get_widget("pacs_tree")
        model, l_iter = tree.get_selection().get_selected()

        try:
            name = model.get_value(l_iter, 2)
        except TypeError:
            return
        
        if name in self.queues["remove"]:
            return
                
        image = model.get_value(l_iter, 0)
        
        if name in self.database.holdPkg:
           dlg = holdpkg_dialog(name, self.icon)
           res = dlg.run()
           dlg.destroy()
           if res == RESPONSE_NO:
               return

        if image == "red":
            return

        if name in self.queues["add"]:
            self.queues["add"].remove(name)

        self.queues["remove"].append(name)
        model.set_value(l_iter, 1, STOCK_REMOVE)
        return

    def remove_from_remove_queue(self, widget, data=None):
        tree = self.gld.get_widget("pacs_tree")
        model, l_iter = tree.get_selection().get_selected()

        try:
            name = model.get_value(l_iter, 2)
        except TypeError:
            return
        
        if not (name in self.queues["remove"]):
            return

        self.queues["remove"].remove(name)
        model.set_value(l_iter, 1, None)
        return

    def execute(self, widget=None, data=None):
        def _req_pac_check(to_check, flag):
            to_do = []
	    try:
		pac = self.database.get_by_name(to_check)
	    except NameError:
		dlg = error_dialog(self.gld.get_widget("main_win"),
		_("%(dep)s is not in the database. %(dep)s is required by %(pkg)s.\nThis maybe either an error in %(pkg)s packaging or a gtkpacman's bug.\nIf you think it's the first, contact the %(pkg)s maintainer, else fill a bug report for gtkpacman, please.") %{'dep': dep, "pkg": name}, self.icon)
		dlg.run()
		dlg.destroy()
		pacs_queues["add"].remove(pac)
		self.queues["add"].remove(name)
		return
	    try:
		if not pac.prop_setted:
		    self.database.set_pac_properties(pac)
	    except:
		return pac, to_do
	    
	    if flag == "req":
		for req in pac.req_by.split(", "):
		    if len(req) >= 1:
			to_do.append(req)
	    else:
		if not pac.installed:
		    for dep in pac.dependencies.split(", "):
			if len(dep) >= 1:
			    to_do.append(dep)
			else:
			    pac = None
		    return pac, to_do
		pac = None
            return pac, to_do

        pacs_queues = { "add": [], "remove": [] }
        deps = []
        
        for name in self.queues["add"]:
            try:
                pac = self.database.get_by_name(name)
            except NameError:
                dlg = error_dialog(self.gld.get_widget("main_win"), _("%s is not in the database.\nThis is probably a bug in gtkpacman. If you think it's so, please send me a bug report.") %name, self.icon)
                dlg.run()
                dlg.destroy()
                continue
            
            if not pac.prop_setted:
                self.database.set_pac_properties(pac)

            pacs_queues["add"].append(pac)
            
            if pac.dependencies:
                dep_todo_list = []
                dep_black_list = []
                deps = pac.dependencies.split(", ")
		for dep in deps:
		    if not dep in self.queues["add"]:
			dep_todo_list.append(dep)
		while dep_todo_list:
		    dep = dep_todo_list.pop(0)
		    if dep.count(">="):
			dep = dep.split(">=")[0]
		    if not (dep in self.queues["add"]):
			done, to_do = _req_pac_check(dep, "dep")
			if done and not done in pacs_queues["add"]:
			    pacs_queues["add"].append(done)
			for add in to_do:
			    if not add in dep_black_list:
				dep_todo_list.append(add)
				dep_black_list.append(add)

        for name in self.queues["remove"]:
            pac = self.database.get_by_name(name)
            if not pac.prop_setted:
                self.database.set_pac_properties(pac)

            pacs_queues["remove"].append(pac)
            if pac.req_by:
                req_pacs = []
                req_todo_list = []
                req_black_list = []
                for req in pac.req_by.split(", "):
                    if not (req in self.queues["remove"]):
                        req_todo_list.append(req)
                while req_todo_list:
                    req = req_todo_list.pop(0)
                    if not (req in self.queues["remove"]):
                        done, to_do = _req_pac_check(req, "req")
                        if done and not done in req_pacs:
                            req_pacs.append(done)
                        for add in to_do:
                            if not add in req_black_list:
                                req_todo_list.append(add)
                                req_black_list.append(add)
                    continue

                if req_pacs:
                    dlg = warning_dialog(self.gld.get_widget("main_win"),
                                     req_pacs, self.icon)
                    if dlg.run() == RESPONSE_YES:
                        pacs_queues["remove"].extend(req_pacs)
                    else:
                        self.queues["remove"].remove(name)
                        pacs_queues["remove"].remove(pac)
                    dlg.destroy()
            continue

        if not (pacs_queues["add"] or pacs_queues["remove"]):
            self._refresh_trees_and_queues()
            return

        retcode = self._confirm(pacs_queues)
        if retcode:
	    self._statusbar(_("Executing queued operations..."))
            dlg = do_dialog(pacs_queues, self.icon)
            dlg.connect("destroy", self._refresh_trees_and_queues, pacs_queues)
            dlg.run()
        else:
            self.queues["add"] = []
            self.queues["remove"] = []
            self._refresh_trees_and_queues()
        return

    def _confirm(self, pacs_queues):
        dlg = confirm_dialog(self.gld.get_widget("main_win"), pacs_queues, self.icon)
        retcode = dlg.run()
        return retcode

    def _refresh_trees_and_queues(self, widget=None, pacs_queues=None):
        self.database.refresh()
        self._refresh_repos_tree()
        
        if pacs_queues:
            for pac in pacs_queues["add"]:
                if not pac.name in self.queues["add"]:
                    self.queues["add"].append(pac.name)

        self._refresh_trees()
        self.queues["add"] = []
        self.queues["remove"] = []
        if pacs_queues:
            for pac in pacs_queues["add"]:
                pac.installed = True
                pac.inst_ver = pac.version
                self.database.set_pac_properties(pac)
                continue
            for pac in pacs_queues["remove"]:
                pac.installed = False
                if pac.repo == 'foreigners':
                    del pac
                    continue
                self.database.set_pac_properties(pac)
                continue
            sum_txt = self.gld.get_widget("summary")
            file_tree = self.gld.get_widget("files")
            sum_buf = sum_txt.get_buffer()
            tree = file_tree.get_model()
            
            try:
                sum_buf.set_text(pac.summary)
                file_model = file_list(pac.filelist)
                file_tree.set_model(file_model)
            except:
                col = file_tree.get_columns()
                tree.clear()
                sum_buf.set_text('')
            
        del(pacs_queues)
	self._statusbar()
	
    def about(self, widget, data=None):
        dlg = about_dialog(self.icon)
        dlg.run()
        dlg.destroy()
        return

    def show_popup(self, widget, event, data=None):
        if event.button == 3:
            self.popup.popup(None, None, None, event.button, event.time)
        else:
            self.popup.popdown()

    def search(self, widget, data=None):	
	win = self.gld.get_widget("main_win")
	wait_cursor = Cursor(WATCH)
	        
        dlg = search_dialog(self.gld.get_widget("main_win"), self.icon)
	
	def _fork():	    
	    repos_tree = self.gld.get_widget("repos_tree")
	    repos_model = repos_tree.get_model()
	    
	    pacs = self.database.get_by_keywords(keywords)	    
	    if self.search_iter:
		repos_model.remove(self.search_iter)
	    self.search_iter = repos_model.append(None, [_("Search results for '%s'") %keywords])
	    self.models["search"] = search_list(pacs)
	    repos_tree.set_cursor_on_cell((1))
	    
	    dlg.destroy()
	    win.window.set_cursor(None)
	
        if dlg.run() == RESPONSE_ACCEPT:
            keywords = dlg.entry.get_text()
	    if keywords:
		dlg.vbox.set_sensitive(False)
		self._statusbar(_("Searching for %s..." %keywords))
		win.window.set_cursor(wait_cursor)
		dlg.window.set_cursor(wait_cursor)
		gobject.idle_add(_fork)	
	    else:
		dlg.destroy()
		error_dlg = error_dialog(None, _("You should insert at least one keyword to search for"), self.icon)
		error_dlg.run()
		error_dlg.destroy()
	else:
	    dlg.destroy()

    def add_from_local_file(self, widget, data=None):
        dlg = local_install_fchooser_dialog(self.gld.get_widget("main_win"),
                                            self.icon)
        if dlg.run() == RESPONSE_ACCEPT:
            fname = dlg.get_filename()
            dlg.destroy()
        else:
            dlg.destroy()
            return
	
	self._statusbar(_("Installing %s" %fname))
        deps, conflicts = self.database.get_local_file_deps(fname)

        install = []
        remove = []
        
        for dep in deps:
	    if dep.count(">="):
		dep = dep.split(">=")[0]
            dep_pkg = self.database.get_by_name(dep)
            if dep_pkg and not dep_pkg.installed:
                install.append(dep_pkg)
            continue

        for conflict in conflicts:
            try:
                conflict_pkg = self.database.get_by_name(conflict)
                remove.append(conflict_pkg)
            except NameError:
                pass
            continue

        pacs_queues = { "add": install, "remove": remove }

        retcode = self._local_confirm(fname, pacs_queues)
        if retcode:
            i_dlg = local_install_dialog(fname, pacs_queues, self.icon)
            i_dlg.connect("destroy", self._after_local_install)
            i_dlg.run()

    def _after_local_install(self, wid, data=None):
        self.database.refresh()
        self.models["foreigners"] = installed_list(self.database["foreigners"])

	self._statusbar()

    def _local_confirm(self, fname, pacs_queue):
        dlg = local_confirm_dialog(self.gld.get_widget("main_win"),
                                   fname, pacs_queue, self.icon)
        if dlg.run():
            retcode = True
        else:
            retcode = False
        return retcode

    def clear_cache(self, wid, data=None):
	self._statusbar(msg=_("Clearing cache..."))
        dlg = command_dialog(self.icon)
        dlg.connect("destroy", self._done)
        dlg.run("Sc")
        return

    def empty_cache(self, wid, data=None):
	self._statusbar(_("Emptying cache..."))
        dlg = command_dialog(self.icon)
        dlg.connect("destroy", self._done)
        dlg.run("Scc")
        return

    def _done(self, widget, data=None):
	self._statusbar()

    def upgrade_system(self, widget, data=None):
        to_upgrade = []
        
        for repo in self.database.values():
            for pac in repo:
                if pac.isold:
                    to_upgrade.append(pac)
                continue
            continue

        if to_upgrade:
            confirm = self._upgrade_confirm(to_upgrade)

            if confirm:
		self._statusbar(_("Refreshing database..."))
                dlg = upgrade_dialog(to_upgrade, self.icon)
                dlg.connect("destroy", self._done_upgrade)
                dlg.run()
        else:
	    self._statusbar(_("There isn't any packages to upgrade"))
        return

    def _upgrade_confirm(self, to_upgrade):
        dlg = upgrade_confirm_dialog(self.gld.get_widget("main_win"),
                                     to_upgrade, self.icon)
        retcode = dlg.run()
        return retcode

    def refresh_database(self, widget, data=None):
	self._statusbar(_("Refreshing database..."))
        dlg = command_dialog(self.icon)
        dlg.connect("destroy", self._done_upgrade)
        dlg.run("Sy")
        return

    def _done_upgrade(self, widget, data=None):
        self.database.refresh()
        self._refresh_repos_tree()
        self._setup_pacs_models()
	self._statusbar(_("Updating compleated"))

    def make_package(self, widget):
        from os import chdir, geteuid, curdir
        from os.path import dirname, abspath
        
        dlg = choose_pkgbuild_dialog(self.gld.get_widget("main_win"), self.icon)
        fname = dlg.run()
        dlg.destroy()
        
        try:
            dname = dirname(fname)
        except:
            return

        pwd = abspath(curdir)
        chdir(dname)

        cdlg = command_dialog(self.icon)

        if geteuid() == 0:
            dlg = change_user_dialog(self.gld.get_widget("main_win"), self.icon)
            user = dlg.run()

            if user == "root":
                cdlg.run("makepkg --asroot -si")
            elif user == "reject":
                pass
            else:
                cdlg.run("su %s -c 'makepkg -si'" %user, False)
            dlg.destroy()
        else:
            cdlg.run("makepkg -si", False)
        chdir(pwd)
	
    def _statusbar(self, msg=None):
	stat_bar = self.gld.get_widget("statusbar")

	if type(msg) == type(()):
	    str = _("%s packages in [ %s ]") %(msg[0], msg[1])
	elif msg == None:
	    str =  _("Done")
	else:
	    str = "%s " %msg
	stat_bar.push(-1, str)
