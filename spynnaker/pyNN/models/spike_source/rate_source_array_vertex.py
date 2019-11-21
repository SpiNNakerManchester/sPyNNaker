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
import numpy
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl)
from spinn_front_end_common.utilities import globals_variables
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)


def _as_numpy_ticks(times, time_step):
    return numpy.ceil(
        numpy.floor(numpy.array(times) * 1000.0) / time_step).astype("int64")


def _send_buffer_times(spike_times, time_step):
    # Convert to ticks
    if len(spike_times) and hasattr(spike_times[0], "__len__"):
        return [_as_numpy_ticks(times, time_step) for times in spike_times]
    else:
        return _as_numpy_ticks(spike_times, time_step)


class RateSourceArrayVertex(
        ReverseIpTagMultiCastSource, SimplePopulationSettable,
        AbstractChangableAfterRun, ProvidesKeyToAtomMappingImpl):
    """ Model for play back of spikes
    """

    RATE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, rate_times, rate_values, constraints, label,
            max_atoms_per_core, model):
        # pylint: disable=too-many-arguments
        self.__model_name = "RateSourceArray"
        self.__model = model

        if rate_times is None:
            rate_times = []
        self._rate_times = rate_times
        time_step = self.get_spikes_sampling_interval()

        super(RateSourceArrayVertex, self).__init__(
            n_keys=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core,
            send_buffer_times=_send_buffer_times(rate_times, time_step),
            send_buffer_partition_id=constants.SPIKE_PARTITION_ID)

        # used for reset and rerun
        self.__requires_mapping = True

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__requires_mapping = False

    @property
    def spike_times(self):
        """ The spike times of the spike source array
        """
        return self._spike_times

    @spike_times.setter
    def spike_times(self, spike_times):
        """ Set the spike source array's spike times. Not an extend, but an\
            actual change

        """
        time_step = self.get_spikes_sampling_interval()
        self.send_buffer_times = _send_buffer_times(spike_times, time_step)
        self._spike_times = spike_times

    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    def describe(self):
        """ Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see ``pyNN.descriptions``).

        If template is None, then a dictionary containing the template\
        context will be returned.
        """

        parameters = dict()
        for parameter_name in self.__model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context
