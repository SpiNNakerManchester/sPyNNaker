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

from collections import Counter
import logging
import numpy
from pyNN.space import Grid2D, Grid3D
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from spinn_utilities.config_holder import get_config_int
from spinn_front_end_common.utility_models import ReverseIpTagMultiCastSource
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.common import PopulationApplicationVertex
from spynnaker.pyNN.models.abstract_models import SupportsStructure
from spynnaker.pyNN.utilities.buffer_data_type import BufferDataType
from spynnaker.pyNN.utilities.ranged import SpynnakerRangedList
from spynnaker.pyNN.models.common import ParameterHolder
from .spike_source_array_machine_vertex import SpikeSourceArrayMachineVertex

logger = FormatAdapter(logging.getLogger(__name__))

# Cutoff to warn too many spikes sent at one time
TOO_MANY_SPIKES = 100


def _as_numpy_ticks(times, time_step):
    return numpy.ceil(
        numpy.floor(numpy.array(times) * 1000.0) / time_step).astype("int64")


def _send_buffer_times(spike_times, time_step):
    # Convert to ticks
    if len(spike_times) and hasattr(spike_times[0], "__len__"):
        data = []
        for times in spike_times:
            data.append(_as_numpy_ticks(times, time_step))
        return data
    else:
        return _as_numpy_ticks(spike_times, time_step)


class SpikeSourceArrayVertex(
        ReverseIpTagMultiCastSource, PopulationApplicationVertex,
        SupportsStructure):
    """
    Model for play back of spikes.
    """

    __slots__ = ["__model_name",
                 "__model",
                 "__structure",
                 "_spike_times",
                 "__n_colour_bits"]

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, spike_times, label,
            max_atoms_per_core, model, splitter, n_colour_bits):
        # pylint: disable=too-many-arguments
        self.__model_name = "SpikeSourceArray"
        self.__model = model
        self.__structure = None

        if spike_times is None:
            spike_times = []
        use_list_as_value = (
            not len(spike_times) or not hasattr(spike_times[0], '__iter__'))
        self._spike_times = SpynnakerRangedList(
            n_neurons, spike_times, use_list_as_value=use_list_as_value)

        time_step = SpynnakerDataView.get_simulation_time_step_us()

        super().__init__(
            n_keys=n_neurons, label=label,
            max_atoms_per_core=max_atoms_per_core,
            send_buffer_times=_send_buffer_times(spike_times, time_step),
            send_buffer_partition_id=constants.SPIKE_PARTITION_ID,
            splitter=splitter)

        self._check_spike_density(spike_times)
        # Do colouring
        self.__n_colour_bits = n_colour_bits
        if self.__n_colour_bits is None:
            self.__n_colour_bits = get_config_int(
                "Simulation", "n_colour_bits")

    @overrides(ReverseIpTagMultiCastSource.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, sdram, label=None):
        send_buffer_times = self._filtered_send_buffer_times(vertex_slice)
        machine_vertex = SpikeSourceArrayMachineVertex(
            label=label, app_vertex=self, vertex_slice=vertex_slice,
            eieio_params=self._eieio_params,
            send_buffer_times=send_buffer_times)
        machine_vertex.enable_recording(self._is_recording)
        # Known issue with ReverseIPTagMulticastSourceMachineVertex
        if sdram:
            assert sdram == machine_vertex.sdram_required
        return machine_vertex

    def _check_spike_density(self, spike_times):
        if len(spike_times):
            if hasattr(spike_times[0], '__iter__'):
                self._check_density_double_list(spike_times)
            else:
                self._check_density_single_list(spike_times)
        else:
            logger.warning("SpikeSourceArray has no spike times")

    def _check_density_single_list(self, spike_times):
        counter = Counter(spike_times)
        top = counter.most_common(1)
        val, count = top[0]
        if count * self.n_atoms > TOO_MANY_SPIKES:
            if self.n_atoms > 1:
                logger.warning(
                    "Danger of SpikeSourceArray sending too many spikes "
                    "at the same time. "
                    "This is because ({}) neurons share the same spike list",
                    self.n_atoms)
            else:
                logger.warning(
                    "Danger of SpikeSourceArray sending too many spikes "
                    "at the same time. "
                    "For example at time {}, {} spikes will be sent",
                    val, count * self.n_atoms)

    def _check_density_double_list(self, spike_times):
        counter = Counter()
        for neuron_id in range(0, self.n_atoms):
            counter.update(spike_times[neuron_id])
        top = counter.most_common(1)
        val, count = top[0]
        if count > TOO_MANY_SPIKES:
            logger.warning(
                "Danger of SpikeSourceArray sending too many spikes "
                "at the same time. "
                "For example at time {}, {} spikes will be sent",
                val, count)

    @overrides(SupportsStructure.set_structure)
    def set_structure(self, structure):
        self.__structure = structure

    @property
    @overrides(ReverseIpTagMultiCastSource.atoms_shape)
    def atoms_shape(self):
        if isinstance(self.__structure, (Grid2D, Grid3D)):
            return self.__structure.calculate_size(self.n_atoms)
        return super(ReverseIpTagMultiCastSource, self).atoms_shape

    def _to_early_spikes_single_list(self, spike_times):
        """
        Checks if there is one or more spike_times before the current time.

        Logs a warning for the first one found

        :param iterable(int) spike_times:
        """
        current_time = SpynnakerDataView.get_current_run_time_ms()
        for i in range(len(spike_times)):
            if spike_times[i] < current_time:
                logger.warning(
                    "SpikeSourceArray {} has spike_times that are lower than "
                    "the current time {} For example {} - "
                    "these will be ignored.",
                    self, current_time, float(spike_times[i]))
                return

    def _check_spikes_double_list(self, spike_times):
        """
        Checks if there is one or more spike_times before the current time.

        Logs a warning for the first one found

        :param iterable(int) spike_times:
        """
        current_time = SpynnakerDataView.get_current_run_time_ms()
        for neuron_id in range(0, self.n_atoms):
            id_times = spike_times[neuron_id]
            for i in range(len(id_times)):
                if id_times[i] < current_time:
                    logger.warning(
                        "SpikeSourceArray {} has spike_times that are lower "
                        "than the current time {} For example {} - "
                        "these will be ignored.",
                        self, current_time, float(id_times[i]))
                    return

    def __set_spike_buffer_times(self, spike_times):
        """
        Set the spike source array's buffer spike times.
        """
        time_step = SpynnakerDataView.get_simulation_time_step_us()
        # warn the user if they are asking for a spike time out of range
        if spike_times:  # in case of empty list do not check
            if hasattr(spike_times[0], '__iter__'):
                self._check_spikes_double_list(spike_times)
            else:
                self._to_early_spikes_single_list(spike_times)
        self.send_buffer_times = _send_buffer_times(spike_times, time_step)
        self._check_spike_density(spike_times)

    def __read_parameter(self, name, selector):
        # pylint: disable=unused-argument
        # This can only be spike times
        return self._spike_times.get_values(selector)

    @overrides(PopulationApplicationVertex.get_parameter_values)
    def get_parameter_values(self, names, selector=None):
        self._check_parameters(names, {"spike_times"})
        return ParameterHolder(names, self.__read_parameter, selector)

    @overrides(PopulationApplicationVertex.set_parameter_values)
    def set_parameter_values(self, name, value, selector=None):
        self._check_parameters(name, {"spike_times"})
        self.__set_spike_buffer_times(value)
        use_list_as_value = (
            not len(value) or not hasattr(value[0], '__iter__'))
        self._spike_times.set_value_by_selector(
            selector, value, use_list_as_value)

    @overrides(PopulationApplicationVertex.get_parameters)
    def get_parameters(self):
        return ["spike_times"]

    @overrides(PopulationApplicationVertex.get_units)
    def get_units(self, name):
        if name == "spikes":
            return ""
        if name == "spike_times":
            return "ms"
        raise KeyError(f"Units for {name} unknown")

    @overrides(PopulationApplicationVertex.get_recordable_variables)
    def get_recordable_variables(self):
        return ["spikes"]

    @overrides(PopulationApplicationVertex.get_buffer_data_type)
    def get_buffer_data_type(self, name):
        if name == "spikes":
            return BufferDataType.EIEIO_SPIKES
        raise KeyError(f"Cannot record {name}")

    @overrides(PopulationApplicationVertex.get_neurons_recording)
    def get_neurons_recording(self, name, vertex_slice):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return vertex_slice.get_raster_ids()

    @overrides(PopulationApplicationVertex.set_recording)
    def set_recording(self, name, sampling_interval=None, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourceArray so being ignored")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(True)
        SpynnakerDataView.set_requires_mapping()

    @overrides(PopulationApplicationVertex.set_not_recording)
    def set_not_recording(self, name, indices=None):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        if indices is not None:
            logger.warning("Indices currently not supported for "
                           "SpikeSourceArray so being ignored")
        self.enable_recording(False)

    @overrides(PopulationApplicationVertex.get_recording_variables)
    def get_recording_variables(self):
        if self._is_recording:
            return ["spikes"]
        return []

    @overrides(PopulationApplicationVertex.get_sampling_interval_ms)
    def get_sampling_interval_ms(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return SpynnakerDataView.get_simulation_time_step_us()

    @overrides(PopulationApplicationVertex.get_recording_region)
    def get_recording_region(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return 0

    @overrides(PopulationApplicationVertex.get_data_type)
    def get_data_type(self, name):
        if name != "spikes":
            raise KeyError(f"Cannot record {name}")
        return None

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template
        together with an associated template engine
        (see :py:mod:`pyNN.descriptions`).

        If template is `None`, then a dictionary containing the template
        context will be returned.
        """
        parameters = self.get_parameter_values(self.__model.default_parameters)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context

    @property
    @overrides(PopulationApplicationVertex.n_colour_bits)
    def n_colour_bits(self):
        return self.__n_colour_bits
