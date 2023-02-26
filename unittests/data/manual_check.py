# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    raise NotImplementedError("OOPS")
except NotSetupException:
    pass
try:
    SpynnakerDataView.get_min_delay()
    raise NotImplementedError("OOPS")
except NotSetupException:
    pass
writer = SpynnakerDataWriter.setup()
try:
    SpynnakerDataView.get_simulation_time_step_us()
    raise NotImplementedError("OOPS")
except DataNotYetAvialable:
    pass
try:
    SpynnakerDataView.get_min_delay()
    raise NotImplementedError("OOPS")
except DataNotYetAvialable:
    pass
writer.set_up_timings_and_delay(1000, 1, 1)
print(SpynnakerDataView.get_simulation_time_step_us())
print(SpynnakerDataView.get_min_delay())
