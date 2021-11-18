# Copyright (c) 2021 The University of Manchester
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

from spinn_front_end_common.utilities.exceptions import (
    SimulatorDataNotYetAvialable, SimulatorNotSetupException)
from spynnaker.pyNN.data import SpynnakerDataView, SpynnakerDataWriter

# This can not be a unittest as the unitest suite would use the same
# python console and therefor the same singleton multiple times

# It can be run multiple time as each run is a new python console

view = SpynnakerDataView()
writer = SpynnakerDataWriter()
try:
    view.machine_time_step
    raise Exception("OOPS")
except SimulatorNotSetupException:
    pass
try:
    view.min_delay
    raise Exception("OOPS")
except SimulatorNotSetupException:
    pass
writer.setup()
try:
    view.machine_time_step
    raise Exception("OOPS")
except SimulatorDataNotYetAvialable:
    pass
try:
    view.min_delay
    raise Exception("OOPS")
except SimulatorDataNotYetAvialable:
    pass
writer.set_machine_time_step(1000)
print(view.machine_time_step)
print(view.min_delay)
