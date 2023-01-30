# Copyright (c) 2023 The University of Manchester
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
import pytest
from spynnaker.pyNN.data.spynnaker_data_view import SpynnakerDataView
import pyNN.spiNNaker as sim


@pytest.fixture(autouse=True)
def check_end_is_called():
    """ Fixture for all tests, to make sure end is used!
    """
    yield
    # If we never setup or we are currently shut down, we are ok
    if not SpynnakerDataView.is_setup() and SpynnakerDataView().is_shutdown():
        return
    sim.end()
    raise Exception("Simulation has not been stopped!")
