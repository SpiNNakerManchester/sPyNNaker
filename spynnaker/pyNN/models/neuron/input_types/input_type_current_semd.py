from data_specification.enums.data_type import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
    SpynakkerRangeDictionary

from .abstract_input_type import AbstractInputType

from enum import Enum

MULTIPLICATOR = "multiplicator"
INH_INPUT_PREVIOUS = "inh_input_previous"


class _CURRENT_SEMD_TYPES(Enum):
    MULTIPLICATOR = (1, DataType.S1615)
    INH_INPUT_PREVIOUS = (2, DataType.S1615)

    def __new__(cls, value, data_type, doc=""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    @property
    def data_type(self):
        return self._data_type


class InputTypeCurrentSEMD(AbstractInputType, AbstractContainsUnits):
    """ The current sEMD input type
    """
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self, n_neurons, multiplicator, inh_input_previous):
        self._units = {
            MULTIPLICATOR: "0",
            INH_INPUT_PREVIOUS: "mV"}

        self._n_neurons = n_neurons
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[MULTIPLICATOR] = multiplicator
        self._data[INH_INPUT_PREVIOUS] = inh_input_previous

    @property
    def multiplicator(self):
        return self._data[MULTIPLICATOR]

    @multiplicator.setter
    def multiplicator(self, multiplicator):
        self._data.set_value(key=MULTIPLICATOR, value=multiplicator)

    @property
    def inh_input_previous(self):
        return self._data[INH_INPUT_PREVIOUS]

    @inh_input_previous.setter
    def inh_input_previous(self, inh_input_previous):
        self._data.set_value(key=INH_INPUT_PREVIOUS, value=inh_input_previous)

    def get_global_weight_scale(self):
        return 1.0

    def get_n_input_type_parameters(self):
        return 2

    def get_input_type_parameters(self):
        return [
            NeuronParameter(self._data[MULTIPLICATOR],
                            _CURRENT_SEMD_TYPES.MULTIPLICATOR.data_type),
            NeuronParameter(self._data[INH_INPUT_PREVIOUS],
                            _CURRENT_SEMD_TYPES.INH_INPUT_PREVIOUS.data_type)
        ]

    def get_input_type_parameter_types(self):
        return [item.data_type for item in _CURRENT_SEMD_TYPES]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):  # n_synapse_types?
        return 1

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
