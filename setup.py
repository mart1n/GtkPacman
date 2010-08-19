#!/usr/bin/env python
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

# classes build, build_locale, install, install_locale are from FreeSpeak.
# These classes are released under the same license of FreeSpeak. Refer to
# FreeSpeak homepage for more information
# FreeSpeak is Copyright(C)2005 by Italian Python Users Group

from distutils.command.build import build as _build
from distutils.command.install import install as _install
from distutils.util import change_root
from distutils.dir_util import mkpath, copy_tree
from distutils import cmd
from distutils.core import setup
import os

class build(_build):
    def __init__(self, *a, **kw):
        self.sub_commands = self.sub_commands + [
            ('build_locale', None),
        ]
        _build.__init__(self, *a, **kw)

class build_locale(cmd.Command):
    user_options = [
        ('build-dir=', 'd', "directory to build to"),
        ('po-dir=', 'd', "directory holding the domain dirs and in them PO-files"),
    ]
    description = 'Build locales'

    def initialize_options(self):
        self.build_dir = 'data/locale'
        self.build_base = None
        self.po_dir = 'data/locale'

    def finalize_options (self):
        self.set_undefined_options('build',
                ('build_base', 'build_base'))
        self.build_dir = change_root(self.build_base, self.build_dir)

    def run(self):
        for po in os.listdir(self.po_dir):
            if not po.endswith('.po'): continue
            locale = po[:-len('.po')]
            path = os.path.join(self.build_dir, locale, 'LC_MESSAGES')
            mkpath(path)
            self.spawn(['msgfmt', '-o',
                    os.path.join(path, '%s.mo' % 'gtkpacman'),
                    os.path.join(self.po_dir, po)])

class install(_install):
    def __init__(self, *a, **kw):
        self.sub_commands = self.sub_commands + [
            ('install_locale', None),
        ]
        _install.__init__(self, *a, **kw)

class install_locale(cmd.Command):
    user_options = [
        ('install-dir=', 'd', "directory to install locales to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('skip-build', None, "skip the build steps"),
    ]
    description = 'Install locales'
    boolean_options = ['skip-build']

    def initialize_options(self):
        self.build_dir = None
        self.install_dir = None
        self.root = None
        self.prefix = None
        self.skip_build = None

    def finalize_options (self):
        self.set_undefined_options('build_locale',
                ('build_dir', 'build_dir'))
        self.set_undefined_options('install',
                ('skip_build', 'skip_build'))
        if self.install_dir is None:
            self.set_undefined_options('install',
                    ('root', 'root'))
            self.set_undefined_options('install',
                    ('prefix', 'prefix'))
            prefix = self.prefix
            if self.root is not None:
                prefix = change_root(self.root, prefix)
            self.install_dir = os.path.join(prefix, 'share', 'locale')

    def run(self):
        if not self.skip_build:
            self.run_command('build_locale')
        copy_tree(src=self.build_dir,
            dst=self.install_dir,
            dry_run=self.dry_run)



setup(cmdclass={'install': install,
                'build': build,
                'build_locale': build_locale,
                'install_locale': install_locale},
      name="gtkpacman",
      version="2.3.1",
      description="Gtk package manager based on pacman",
      author="Stefano Esposito", author_email="ragnarok@email.it",
      url="http://gtkpacman.berlios.de",
      license="GNU General Public License",
      packages=["gtkPacman"],
      scripts=["gtkpacman"],
      data_files=[('share/gtkpacman/icons', ["data/icons/blank_box.png",
                                             "data/icons/green_box.png",
                                             "data/icons/pacman.png",
                                             "data/icons/red_box.png",
                                             "data/icons/yellow_box.png"]),
                  ('share/gtkpacman', ["data/gtkpacman.glade"]),
                  ('share/applications', ["data/gtkpacman.desktop"]),
                  ('share/pixmaps',  ["data/icons/pacman.png"])
                  ]
      )
