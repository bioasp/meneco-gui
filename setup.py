# Copyright (c) 2015, Sven Thiele <sthiele78@gmail.com>
#
# This file is part of meneco-gui.
#
# meneco-gui is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# meneco-gui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ingranalyze.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-
from setuptools import setup
import os
import sys
import platform
import distutils
import site
import sysconfig

from setuptools.command.install import install as _install



class install(_install):
    def run(self):
        _install.run(self)
                         
setup(cmdclass={'install': install},
      name='meneco-gui',
      version='1.1',
      url='http://bioasp.github.io/meneco/',
      license='GPLv3+',
      description='A graphical user interface for meneco.',
      long_description=open('README.rst').read(),
      author='Sven Thiele',
      author_email='sthiele78@gmail.com',
      scripts = ['meneco-gui.py'],
      install_requires=[
        "meneco == 1.4.2"        
       ,#"PyQt4 == 4.11.1"
      ]
)
