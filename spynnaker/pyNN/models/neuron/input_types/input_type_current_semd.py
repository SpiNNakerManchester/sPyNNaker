from data_specification.enums.data_type import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .abstract_input_type import AbstractInputType

from enum import Enum


class _CURRENT_SEMD_TYPES(Enum):
    MULTIPLICATOR = (1, DataType.S1615)
    INH_INPUT_PREVIOUS = (2, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class InputTypeCurrentSEMD(AbstractInputType, AbstractContainsUnits):
    """ The current sEMD input type
    """

    def __init__(self, n_neurons, multiplicator, inh_input_previous):
        AbstractInputType.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            "multiplicator": "0",
            "inh_input_previous": "mV"}

        self._n_neurons = n_neurons
        self._multiplicator = utility_calls.convert_param_to_numpy(
            multiplicator, n_neurons)
        self._inh_input_previous = utility_calls.convert_param_to_numpy(
            inh_input_previous, n_neurons)

    @property
    def multiplicator(self):
        return self._multiplicator

    @multiplicator.setter
    def multiplicator(self, multiplicator):
        self._multiplicator = utility_calls.convert_param_to_numpy(
            multiplicator, self._n_neurons)

    @property
    def inh_input_previous(self):
        return self._inh_input_previous

    @inh_input_previous.setter
    def inh_input_previous(self, inh_input_previous):
        self._inh_input_previous = utility_calls.convert_param_to_numpy(
            inh_input_previous, self._n_neurons)

    def get_global_weight_scale(self):
        return 1.0

    def get_n_input_type_parameters(self):
        return 2

    def get_input_type_parameters(self):
        return [
            NeuronParameter(self._multiplicator,
                            _CURRENT_SEMD_TYPES.MULTIPLICATOR.data_type),
            NeuronParameter(self._inh_input_previous,
                            _CURRENT_SEMD_TYPES.INH_INPUT_PREVIOUS.data_type)
        ]

    def get_input_type_parameter_types(self):
        return [item.data_type for item in _CURRENT_SEMD_TYPES]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):  #n_synapse_types?
        return 0

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
