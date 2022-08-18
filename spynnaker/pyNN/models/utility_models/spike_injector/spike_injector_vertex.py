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
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import EIEIOSpikeRecorder
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.abstract_models import (
    PopulationApplicationVertex, RecordingType)

logger = FormatAdapter(logging.getLogger(__name__))


class SpikeInjectorVertex(
        ReverseIpTagMultiCastSource, PopulationApplicationVertex):
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
            injection_partition_id=SPIKE_PARTITION_ID,
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

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self):
        return ["spikes"]

    @overrides(PopulationApplicationVertex.can_record)
    def can_record(self, name):
        return name == "spikes"

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name, sampling_interval=None, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        self.enable_recording(True)
        self.__spike_recorder.record = True

    @overrides(PopulationApplicationVertex.get_recording_variables)
    def get_recording_variables(self):
        if self.__spike_recorder.record:
            return ["spikes"]
        return []

    @overrides(PopulationApplicationVertex.is_recording_variable)
    def is_recording_variable(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return self.__spike_recorder.record

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(False)
        self.__spike_recorder.record = False

    @overrides(PopulationApplicationVertex.get_recorded_data)
    def get_recorded_data(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return self.__spike_recorder.get_spikes(
            self.label, SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID, self,
            lambda vertex:
                vertex.virtual_key
                if vertex.virtual_key is not None
                else 0)

    @overrides(PopulationApplicationVertex.get_recording_sampling_interval)
    def get_recording_sampling_interval(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return SpynnakerDataView.get_simulation_time_step_us()

    @overrides(PopulationApplicationVertex.get_recording_indices)
    def get_recording_indices(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return range(self.n_atoms)

    @overrides(PopulationApplicationVertex.get_recording_type)
    def get_recording_type(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return RecordingType.BIT_FIELD

    @overrides(PopulationApplicationVertex.clear_recording_data)
    def clear_recording_data(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        buffer_manager = SpynnakerDataView.get_buffer_manager()
        for machine_vertex in self.machine_vertices:
            placement = SpynnakerDataView.get_placement_of_vertex(
                machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeInjectorVertex.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is None, then a dictionary containing the template context
        will be returned.
        """

        parameters = self.get_parameter_values(self.default_parameters)

        context = {
            "name": "SpikeInjector",
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": parameters,
        }
        return context
