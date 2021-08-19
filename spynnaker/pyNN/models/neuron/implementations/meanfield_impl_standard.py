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

import numpy

from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from .abstract_neuron_impl import AbstractNeuronImpl
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD

# The size of the n_steps_per_timestep parameter
_N_STEPS_PER_TIMESTEP_SIZE = 1 * BYTES_PER_WORD

# The default number of steps per timestep
_DEFAULT_N_STEPS_PER_TIMESTEP = 1


class MeanfieldImplStandard(AbstractNeuronImpl):
    """ The standard componentised meanfield implementation.
    """

    __slots__ = [
        "__model_name",
        "__binary",
        "__neuron_model",
        "__config",
        "__mathsbox",
        "__input_type",
        "__synapse_type",
        "__threshold_type",
        "__additional_input_type",
        "__components",
        "__n_steps_per_timestep"
    ]

    # _RECORDABLES = ["Ve", "gsyn_exc", "gsyn_inh"]
    _RECORDABLES = ["Ve", "muV", "sV", "muGn", "TvN", "Vthre",
                    "Fout_th", "err_func",  "gsyn_exc", "gsyn_inh"]

    # _RECORDABLE_DATA_TYPES = {
    #     "Ve": DataType.S1615,
    #     "gsyn_exc": DataType.S1615,
    #     "gsyn_inh": DataType.S1615
    # }
    _RECORDABLE_DATA_TYPES = {
        "Ve": DataType.S1615,
        "muV": DataType.S1615,
        "sV": DataType.S1615,
        "muGn": DataType.S1615,
        "TvN": DataType.S1615,
        "Vthre": DataType.S1615,
        "Fout_th": DataType.S1615,
        "err_func": DataType.S1615,
        "gsyn_exc": DataType.S1615,
        "gsyn_inh": DataType.S1615
    }

    # _RECORDABLE_UNITS = {
    #     'Ve': 'mV',
    #     'gsyn_exc': "uS",
    #     'gsyn_inh': "uS"
    # }
    _RECORDABLE_UNITS = {
        'Ve': 'mV',
        'muV': "uS",
        'sV': "uS",
        'TvN': 'mV',
        'Vthre': "uS",
        'Fout_th': "uS",
        'err_func': 'mV',
        'gsyn_exc': "uS",
        'gsyn_inh': "uS"
    }

    def __init__(
            self, model_name, binary, neuron_model, config, mathsbox,
            input_type, synapse_type, threshold_type,
            additional_input_type=None):
        """
        :param str model_name:
        :param str binary:
        :param AbstractNeuronModel neuron_model:
        :param AbstractInputType input_type:
        :param AbstractSynapseType synapse_type:
        :param AbstractThresholdType threshold_type:
        :param additional_input_type:
        :type additional_input_type: AbstractAdditionalInput or None
        """
        self.__model_name = model_name
        self.__binary = binary
        self.__neuron_model = neuron_model
        self.__config = config
        self.__mathsbox = mathsbox
        self.__input_type = input_type
        self.__synapse_type = synapse_type
        self.__threshold_type = threshold_type
        self.__additional_input_type = additional_input_type
        self.__n_steps_per_timestep = _DEFAULT_N_STEPS_PER_TIMESTEP

        self.__components = [
            self.__neuron_model, self.__config, self.__mathsbox,
            self.__input_type, self.__threshold_type, self.__synapse_type]
        if self.__additional_input_type is not None:
            self.__components.append(self.__additional_input_type)

    @property
    def n_steps_per_timestep(self):
        return self.__n_steps_per_timestep

    @n_steps_per_timestep.setter
    def n_steps_per_timestep(self, n_steps_per_timestep):
        self.__n_steps_per_timestep = n_steps_per_timestep

    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self):
        return self.__model_name

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self):
        return self.__binary

    @overrides(AbstractNeuronImpl.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        total = self.__neuron_model.get_n_cpu_cycles(n_neurons)
        total += self.__synapse_type.get_n_cpu_cycles(n_neurons)
        total += self.__config.get_n_cpu_cycles(n_neurons)
        total += self.__input_type.get_n_cpu_cycles(n_neurons)
        total += self.__mathsbox.get_n_cpu_cycles(n_neurons)
        total += self.__threshold_type.get_n_cpu_cycles(n_neurons)
        if self.__additional_input_type is not None:
            total += self.__additional_input_type.get_n_cpu_cycles(n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        total = _N_STEPS_PER_TIMESTEP_SIZE
        total += self.__neuron_model.get_dtcm_usage_in_bytes(n_neurons)
        total += self.__synapse_type.get_dtcm_usage_in_bytes(n_neurons)
        total += self.__config.get_dtcm_usage_in_bytes(n_neurons)
        total += self.__input_type.get_dtcm_usage_in_bytes(n_neurons)
        total += self.__mathsbox.get_dtcm_usage_in_bytes(n_neurons)
        total += self.__threshold_type.get_dtcm_usage_in_bytes(n_neurons)
        if self.__additional_input_type is not None:
            total += self.__additional_input_type.get_dtcm_usage_in_bytes(
                n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        total = _N_STEPS_PER_TIMESTEP_SIZE
        total += self.__neuron_model.get_sdram_usage_in_bytes(n_neurons)
        total += self.__synapse_type.get_sdram_usage_in_bytes(n_neurons)
        total += self.__config.get_sdram_usage_in_bytes(n_neurons)
        total += self.__input_type.get_sdram_usage_in_bytes(n_neurons)
        total += self.__mathsbox.get_sdram_usage_in_bytes(n_neurons)
        total += self.__threshold_type.get_sdram_usage_in_bytes(n_neurons)
        if self.__additional_input_type is not None:
            total += self.__additional_input_type.get_sdram_usage_in_bytes(
                n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self):
        return self.__input_type.get_global_weight_scale()

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self):
        return self.__synapse_type.get_n_synapse_types()

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        return self.__synapse_type.get_synapse_id_by_target(target)

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self):
        return self.__synapse_type.get_synapse_targets()

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self):
        return self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable):
        return self._RECORDABLE_UNITS[variable]

    @overrides(AbstractNeuronImpl.get_recordable_data_types)
    def get_recordable_data_types(self):
        return self._RECORDABLE_DATA_TYPES

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable):
        return variable in self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable):
        return self._RECORDABLES.index(variable)

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters):
        for component in self.__components:
            component.add_parameters(parameters)

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self, state_variables):
        for component in self.__components:
            component.add_state_variables(state_variables)

    @overrides(AbstractNeuronImpl.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):
        # Work out the time step per step
        ts = globals_variables.get_simulator().machine_time_step
        ts /= self.__n_steps_per_timestep
        items = [numpy.array([self.__n_steps_per_timestep], dtype="uint32")]
        items.extend(
            component.get_data(parameters, state_variables, vertex_slice, ts)
            for component in self.__components)
        return numpy.concatenate(items)

    @overrides(AbstractNeuronImpl.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        offset += _N_STEPS_PER_TIMESTEP_SIZE
        for component in self.__components:
            offset = component.read_data(
                data, offset, vertex_slice, parameters, state_variables)
        return offset

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable):
        for component in self.__components:
            if component.has_variable(variable):
                return component.get_units(variable)

        raise KeyError(
            "The parameter {} does not exist in this input "
            "conductance component".format(variable))

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self):
        return isinstance(self.__input_type, InputTypeConductance)

    def __getitem__(self, key):
        # Find the property in the components...
        for component in self.__components:
            if hasattr(component, key):
                return getattr(component, key)
        # ... or fail
        raise AttributeError("'{}' object has no attribute {}".format(
            self.__class__.__name__, key))
