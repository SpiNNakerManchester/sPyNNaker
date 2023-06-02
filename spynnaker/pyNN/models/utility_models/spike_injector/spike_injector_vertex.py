# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from pyNN.space import Grid2D, Grid3D
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.common import EIEIOSpikeRecorder
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType
from spynnaker.pyNN.utilities.constants import SPIKE_PARTITION_ID
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.abstract_models import SupportsStructure

logger = FormatAdapter(logging.getLogger(__name__))


class SpikeInjectorVertex(
        ReverseIpTagMultiCastSource, PopulationApplicationVertex,
        SupportsStructure):
    """
    An Injector of Spikes for PyNN populations.  This only allows the user
    to specify the virtual_key of the population to identify the population.
    """
    __slots__ = (
        "__spike_recorder",
        "__structure")

    default_parameters = {
        'label': "spikeInjector", 'port': None, 'virtual_key': None}

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, label, port, virtual_key,
            reserve_reverse_ip_tag, splitter):
        # pylint: disable=too-many-arguments
        super().__init__(
            n_keys=n_neurons, label=label, receive_port=port,
            virtual_key=virtual_key,
            reserve_reverse_ip_tag=reserve_reverse_ip_tag,
            injection_partition_id=SPIKE_PARTITION_ID,
            splitter=splitter)

        # Set up for recording
        self.__spike_recorder = EIEIOSpikeRecorder()
        self.__structure = None

    @overrides(SupportsStructure.set_structure)
    def set_structure(self, structure):
        self.__structure = structure

    @property
    @overrides(PopulationApplicationVertex.atoms_shape)
    def atoms_shape(self):
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.n_atoms)
        return super().atoms_shape

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self):
        return ["spikes"]

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name, sampling_interval=None, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeInjector so being ignored")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeInjector so being ignored")
        self.enable_recording(True)
        self.__spike_recorder.record = True

    @overrides(PopulationApplicationVertex.get_recording_variables)
    def get_recording_variables(self):
        if self.__spike_recorder.record:
            return ["spikes"]
        return []

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(False)
        self.__spike_recorder.record = False

    @overrides(PopulationApplicationVertex.get_sampling_interval_ms)
    def get_sampling_interval_ms(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return SpynnakerDataView.get_simulation_time_step_us()

    @overrides(PopulationApplicationVertex.get_data_type)
    def get_data_type(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return None

    @overrides(PopulationApplicationVertex.get_buffer_data_type)
    def get_buffer_data_type(self, name):
        if name == "spikes":
            return BufferDataType.EIEIO_SPIKES
        raise KeyError(f"Cannot record {name}")

    @overrides(PopulationApplicationVertex.get_units)
    def get_units(self, name):
        if name == "spikes":
            return ""
        raise KeyError(f"Cannot record {name}")

    @overrides(PopulationApplicationVertex.get_recording_region)
    def get_recording_region(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return 0

    @overrides(PopulationApplicationVertex.get_neurons_recording)
    def get_neurons_recording(self, name, vertex_slice):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return vertex_slice.get_raster_ids()

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is `None`, then a dictionary containing the template
        context will be returned.
        """
        context = {
            "name": "SpikeInjector",
            "default_parameters": self.default_parameters,
            "default_initial_values": self.default_parameters,
            "parameters": {
                "port": self._eieio_params.receive_port,
                "virtual_key": self._eieio_params.virtual_key},
        }
        return context
