from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .abstract_neuron_impl import AbstractNeuronImpl

from data_specification.enums.data_type import DataType

from enum import Enum


class _STATIC_TYPES(Enum):
    EXC_INPUT = (1, DataType.S1615)
    INH_INPUT = (2, DataType.S1615)
    EXC_INPUT_VALUE = (3, DataType.S1615)
    INH_INPUT_VALUE = (4, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class NeuronImplSEMD(AbstractNeuronImpl, AbstractContainsUnits):
    """ The sEMD implementation of the neuron model
    """

    def __init__(self, n_neurons, exc_input, inh_input,
                 exc_input_value, inh_input_value):
        AbstractNeuronImpl.__init__(self)
        AbstractContainsUnits.__init__(self)

#        self._units = {'v_thresh': "mV"}

        self._n_neurons = n_neurons
        self._v_thresh = utility_calls.convert_param_to_numpy(
            v_thresh, n_neurons)

    def __init__(self):
        AbstractNeuronImpl.__init__(self)
        AbstractContainsUnits.__init__(self)
        self._units = {}

    def get_global_weight_scale(self):
        return 1.0

    def get_n_neuron_impl_parameters(self):
        return 4

    def get_neuron_impl_parameters(self):
        return []

    def get_neuron_impl_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self, n_neuron_impl):
        return 0

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
