from data_specification.enums.data_type import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models.abstract_contains_units import \
    AbstractContainsUnits
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.input_types.abstract_input_type \
    import AbstractInputType

from enum import Enum


class _CONDUCTANTCE_TYPES(Enum):
    E_REV_E = (1, DataType.S1615)
    E_REV_I = (2, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class InputTypeConductance(AbstractInputType, AbstractContainsUnits):
    """ The conductance input type
    """

    def __init__(self, n_neurons, e_rev_E, e_rev_I):
        AbstractInputType.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            "e_rev_I": "mV",
            "e_rev_E": "mV"}

        self._n_neurons = n_neurons
        self._e_rev_E = utility_calls.convert_param_to_numpy(
            e_rev_E, n_neurons)
        self._e_rev_I = utility_calls.convert_param_to_numpy(
            e_rev_I, n_neurons)

    @property
    def e_rev_E(self):
        return self._e_rev_E

    @e_rev_E.setter
    def e_rev_E(self, e_rev_E):
        self._e_rev_E = utility_calls.convert_param_to_numpy(
            e_rev_E, self._n_neurons)

    @property
    def e_rev_I(self):
        return self._e_rev_I

    @e_rev_I.setter
    def e_rev_I(self, e_rev_I):
        self._e_rev_I = utility_calls.convert_param_to_numpy(
            e_rev_I, self._n_neurons)

    def get_global_weight_scale(self):
        return 1024.0

    def get_n_input_type_parameters(self):
        return 2

    def get_input_type_parameters(self):
        return [
            NeuronParameter(
                self._e_rev_E, _CONDUCTANTCE_TYPES.E_REV_E.data_type),
            NeuronParameter(
                self._e_rev_I, _CONDUCTANTCE_TYPES.E_REV_I.data_type)
        ]

    def get_input_type_parameter_types(self):
        return [item.data_type for item in _CONDUCTANTCE_TYPES]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        return 10

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
