from .abstract_neuron_impl import AbstractNeuronImpl
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spinn_utilities.overrides import overrides
import numpy


class NeuronImplStandard(AbstractNeuronImpl):
    """ The standard neuron implementation, consisting of various components
    """

    __slots__ = [
        "_model_name",
        "_binary",
        "_neuron_model",
        "_input_type",
        "_synapse_type",
        "_threshold_type",
        "_additional_input_type",
        "_components"
    ]

    _RECORDABLES = ["v", "gsyn_exc", "gsyn_inh"]

    _RECORDABLE_UNITS = {
        'spikes': 'spikes',
        'v': 'mV',
        'gsyn_exc': "uS",
        'gsyn_inh': "uS"}

    def __init__(
            self, model_name, binary, neuron_model, input_type,
            synapse_type, threshold_type, additional_input_type=None):
        self._model_name = model_name
        self._binary = binary
        self._neuron_model = neuron_model
        self._input_type = input_type
        self._synapse_type = synapse_type
        self._threshold_type = threshold_type
        self._additional_input_type = additional_input_type

        self._components = [
            self._neuron_model, self._input_type, self._threshold_type,
            self._synapse_type]
        if self._additional_input_type is not None:
            self._components.append(self._additional_input_type)

    @property
    @overrides(AbstractNeuronImpl.model_name)
    def model_name(self):
        return self._model_name

    @property
    @overrides(AbstractNeuronImpl.binary_name)
    def binary_name(self):
        return self._binary

    @overrides(AbstractNeuronImpl.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        total = self._neuron_model.get_n_cpu_cycles(n_neurons)
        total += self._synapse_type.get_n_cpu_cycles(n_neurons)
        total += self._input_type.get_n_cpu_cycles(n_neurons)
        total += self._threshold_type.get_n_cpu_cycles(n_neurons)
        if self._additional_input_type is not None:
            total += self._additional_input_type.get_n_cpu_cycles(n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        total = self._neuron_model.get_dtcm_usage_in_bytes(n_neurons)
        total += self._synapse_type.get_dtcm_usage_in_bytes(n_neurons)
        total += self._input_type.get_dtcm_usage_in_bytes(n_neurons)
        total += self._threshold_type.get_dtcm_usage_in_bytes(n_neurons)
        if self._additional_input_type is not None:
            total += self._additional_input_type.get_dtcm_usage_in_bytes(
                n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        total = self._neuron_model.get_sdram_usage_in_bytes(n_neurons)
        total += self._synapse_type.get_sdram_usage_in_bytes(n_neurons)
        total += self._input_type.get_sdram_usage_in_bytes(n_neurons)
        total += self._threshold_type.get_sdram_usage_in_bytes(n_neurons)
        if self._additional_input_type is not None:
            total += self._additional_input_type.get_sdram_usage_in_bytes(
                n_neurons)
        return total

    @overrides(AbstractNeuronImpl.get_global_weight_scale)
    def get_global_weight_scale(self):
        return self._input_type.get_global_weight_scale()

    @overrides(AbstractNeuronImpl.get_n_synapse_types)
    def get_n_synapse_types(self):
        return self._synapse_type.get_n_synapse_types()

    @overrides(AbstractNeuronImpl.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        return self._synapse_type.get_synapse_id_by_target(target)

    @overrides(AbstractNeuronImpl.get_synapse_targets)
    def get_synapse_targets(self):
        return self._synapse_type.get_synapse_targets()

    @overrides(AbstractNeuronImpl.get_recordable_variables)
    def get_recordable_variables(self):
        return self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_units)
    def get_recordable_units(self, variable):
        return self._RECORDABLE_UNITS[variable]

    @overrides(AbstractNeuronImpl.is_recordable)
    def is_recordable(self, variable):
        return variable in self._RECORDABLES

    @overrides(AbstractNeuronImpl.get_recordable_variable_index)
    def get_recordable_variable_index(self, variable):
        return self._RECORDABLES.index(variable)

    @overrides(AbstractNeuronImpl.add_parameters)
    def add_parameters(self, parameters):
        for component in self._components:
            component.add_parameters(parameters)

    @overrides(AbstractNeuronImpl.add_state_variables)
    def add_state_variables(self, state_variables):
        for component in self._components:
            component.add_state_variables(state_variables)

    @overrides(AbstractNeuronImpl.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):
        return numpy.concatenate([
            component.get_data(parameters, state_variables, vertex_slice)
            for component in self._components
        ])

    @overrides(AbstractNeuronImpl.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        for component in self._components:
            offset = component.read_data(
                data, offset, vertex_slice, parameters, state_variables)
        return offset

    @overrides(AbstractNeuronImpl.get_units)
    def get_units(self, variable):
        for component in self._components:
            if component.has_variable(variable):
                return component.get_units(variable)

        raise KeyError(
            "The parameter {} does not exist in this input "
            "conductance component".format(variable))

    @property
    @overrides(AbstractNeuronImpl.is_conductance_based)
    def is_conductance_based(self):
        return isinstance(self._input_type, InputTypeConductance)

    def __getitem__(self, key):
        # Find the property in the components...
        for component in self._components:
            if hasattr(component, key):
                return getattr(component, key)
        # ... or fail
        raise AttributeError("'{}' object has no attribute {}".format(
            self.__class__.__name__, key))

    def __setitem__(self, key, value):
        # Find the property in the components...
        for component in self._components:
            if hasattr(component, key):
                return setattr(component, key, value)
        # ... or fail
        raise AttributeError("'{}' object has no attribute {}".format(
            self.__class__.__name__, key))
