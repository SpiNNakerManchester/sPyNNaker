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

from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.failed_state import (
    FailedState, FAILED_STATE_MSG)
from spynnaker.pyNN.spynnaker_simulator_interface import (
    SpynnakerSimulatorInterface)


class SpynnakerFailedState(SpynnakerSimulatorInterface, FailedState, object):
    """ Marks the simulation as failed.
    """

    __slots__ = ()

    def get_current_time(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def has_reset_last(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def max_delay(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def min_delay(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @staticmethod
    def reset(annotations=None):
        raise ConfigurationException(FAILED_STATE_MSG)

    def set_number_of_neurons_per_core(self, neuron_type, max_permitted):
        raise ConfigurationException(FAILED_STATE_MSG)
