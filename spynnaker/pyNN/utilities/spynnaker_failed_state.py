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

import logging
from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.config_handler import ConfigHandler
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spinn_front_end_common.utilities.failed_state import (
    FailedState, FAILED_STATE_MSG)
from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon
from spynnaker.pyNN.spynnaker_simulator_interface import (
    SpynnakerSimulatorInterface)
logger = FormatAdapter(logging.getLogger(__name__))


class SpynnakerFailedState(
        SpynnakerSimulatorInterface, FailedState, metaclass=AbstractBase):
    """ Marks the simulation as failed.
    """

    __slots__ = ("write_on_end", "_name")

    def __init__(self, name):
        self._name = name
        self.write_on_end = []

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

    @property
    def dt(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def mpi_rank(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def num_processes(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def recorders(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def segment_counter(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def t(self):
        raise ConfigurationException(FAILED_STATE_MSG)

    @property
    def name(self):
        return self._name

    @property
    @overrides(FailedState.config)
    def config(self):
        logger.warning(
            "Accessing config before setup is not recommended as setup could"
            " change some config values. ")
        handler = ConfigHandler(
            AbstractSpiNNakerCommon.CONFIG_FILE_NAME,
            [AbstractSpiNNakerCommon.extended_config_path()], [])
        return handler.config
