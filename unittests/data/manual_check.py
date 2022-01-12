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

from spinn_utilities.config_holder import clear_cfg_files
from spinn_utilities.exceptions import (
    DataNotYetAvialable, NotSetupException)
from spynnaker.pyNN.config_setup import add_spynnaker_cfg
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.data.spynnaker_data_writer import SpynnakerDataWriter

# This can not be a unittest as the unitest suite would use the same
# python console and therefor the same singleton multiple times

# It can be run multiple time as each run is a new python console
# reset the configs without mocking the global data
clear_cfg_files(True)
add_spynnaker_cfg()

try:
    SpynnakerDataView.get_simulation_time_step_us()
    raise Exception("OOPS")
except NotSetupException:
    pass
try:
    SpynnakerDataView.get_min_delay()
    raise Exception("OOPS")
except NotSetupException:
    pass
writer = SpynnakerDataWriter.setup()
try:
    SpynnakerDataView.get_simulation_time_step_us()
    raise Exception("OOPS")
except DataNotYetAvialable:
    pass
try:
    SpynnakerDataView.get_min_delay()
    raise Exception("OOPS")
except DataNotYetAvialable:
    pass
writer.set_up_timings_and_delay(1000, 1, 1)
print(SpynnakerDataView.get_simulation_time_step_us())
print(SpynnakerDataView.get_min_delay())
