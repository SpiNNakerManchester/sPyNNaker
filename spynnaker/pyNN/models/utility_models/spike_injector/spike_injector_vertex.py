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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from spinn_front_end_common.abstract_models import (
    AbstractProvidesOutgoingPartitionConstraints)
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, EIEIOSpikeRecorder, SimplePopulationSettable)

logger = FormatAdapter(logging.getLogger(__name__))


class SpikeInjectorVertex(
        ReverseIpTagMultiCastSource, SimplePopulationSettable,
        AbstractProvidesOutgoingPartitionConstraints, AbstractSpikeRecordable):
    """ An Injector of Spikes for PyNN populations.  This only allows the user\
        to specify the virtual_key of the population to identify the population
    """
    __slots__ = [
        "__receive_port",
        "__spike_recorder",
        "__virtual_key"]

    default_parameters = {
        'label': "spikeInjector", 'port': None, 'virtual_key': None}

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, label, constraints, port, virtual_key,
            reserve_reverse_ip_tag, splitter):
        # pylint: disable=too-many-arguments
        self.__receive_port = None
        self.__virtual_key = None

        super().__init__(
            n_keys=n_neurons, label=label, receive_port=port,
            virtual_key=virtual_key,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag,
            constraints=constraints,
            enable_injection=True,
            splitter=splitter)

        # Set up for recording
        self.__spike_recorder = EIEIOSpikeRecorder()

    @property
    def port(self):
        return self.__receive_port

    @port.setter
    def port(self, port):
        self.__receive_port = port

    @property
    def virtual_key(self):
        return self.__virtual_key

    @virtual_key.setter
    def virtual_key(self, virtual_key):
        self.__virtual_key = virtual_key

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported "
                           "so being ignored")
        if indexes is not None:
            logger.warning("Indexes currently not supported "
                           "so being ignored")
        self.enable_recording(new_state)
        self.__spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return SpynnakerDataView().simulation_time_step_us

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(self,
                   buffer_manager):
        return self.__spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID, self,
            lambda vertex:
                vertex.virtual_key
                if vertex.virtual_key is not None
                else 0)

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager):
        for machine_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        constraints = super().get_outgoing_partition_constraints(partition)
        constraints.append(ContiguousKeyRangeContraint())
        return constraints

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is None, then a dictionary containing the template context
        will be returned.
        """

        parameters = dict()
        for parameter_name in self.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": "SpikeInjector",
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": parameters,
        }
        return context
