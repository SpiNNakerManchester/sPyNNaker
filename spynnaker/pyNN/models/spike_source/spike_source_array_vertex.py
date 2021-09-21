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
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, EIEIOSpikeRecorder, SimplePopulationSettable)
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


class SpikeSourceArrayVertex(
        ReverseIpTagMultiCastSource, AbstractSpikeRecordable,
        SimplePopulationSettable, AbstractChangableAfterRun,
        ProvidesKeyToAtomMappingImpl):
    """ Model for play back of spikes
    """

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, spike_times, constraints, label,
            max_atoms_per_core, model):
        # pylint: disable=too-many-arguments
        self.__model_name = "SpikeSourceArray"
        self.__model = model

        if spike_times is None:
            spike_times = []
        self._spike_times = spike_times
        time_step = self.get_spikes_sampling_interval()

        super(SpikeSourceArrayVertex, self).__init__(
            n_keys=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core,
            send_buffer_times=_send_buffer_times(spike_times, time_step),
            send_buffer_partition_id=constants.SPIKE_PARTITION_ID)

        # handle recording
        self.__spike_recorder = EIEIOSpikeRecorder()

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

    @property
    def slice_list(self):
        # to be extended when moving to multiple partitions
        return [self]

    @spike_times.setter
    def spike_times(self, spike_times):
        """ Set the spike source array's spike times. Not an extend, but an\
            actual change
        """
        time_step = self.get_spikes_sampling_interval()
        self.send_buffer_times = _send_buffer_times(spike_times, time_step)
        self._spike_times = spike_times

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourceArray so being ignored")
        if indexes is not None:
            logger.warning("Indexes currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(new_state)
        self.__requires_mapping = not self.__spike_recorder.record
        self.__spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(
            self, placements, graph_mapper, buffer_manager, machine_time_step):
        return self.__spike_recorder.get_spikes(
            self.label, buffer_manager, 0,
            placements, graph_mapper, self,
            lambda vertex:
                vertex.virtual_key
                if vertex.virtual_key is not None
                else 0,
            machine_time_step)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements, graph_mapper):
        machine_vertices = graph_mapper.get_machine_vertices(self)
        for machine_vertex in machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourceArrayVertex.SPIKE_RECORDING_REGION_ID)

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