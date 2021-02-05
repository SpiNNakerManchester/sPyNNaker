# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
A simple script to generate connection data for
test_from_file_connector_large.py.
"""

import os
import random
import numpy

connection_list = []
for i in range(255):
    connection_list.append(
        (i, random.randint(0, 255), random.random(), random.randint(10, 15)))

current_file_path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_file_path, "large.connections")
if os.path.exists(path):
    os.remove(path)

numpy.savetxt(path, connection_list)
