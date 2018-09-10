from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary

from .abstract_input_type import AbstractInputType

from enum import Enum

E_REV_E = "e_rev_E"
E_REV_E2 = "e_rev_E2"
E_REV_I = "e_rev_I"
E_REV_I2 = "e_rev_I2"


class _2E2I_CONDUCTANTCE_TYPES(Enum):
    E_REV_E = (1, DataType.S1615)
    E_REV_E2 = (2, DataType.S1615)
    E_REV_I = (3, DataType.S1615)
    E_REV_I2 = (4, DataType.S1615)

    def __new__(cls, value, data_type, doc=""):
        # pylint: disable=protected-access
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        obj.__doc__ = doc
        return obj

    @property
    def data_type(self):
        return self._data_type


class InputTypeConductance2E2I(AbstractInputType, AbstractContainsUnits):
    """ The conductance input type
    """
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self,
                 n_neurons,
                 e_rev_E,
                 e_rev_E2,
                 e_rev_I,
                 e_rev_I2
                 ):
        self._units = {
            E_REV_E: "mV",
            E_REV_E2: "mV",
            E_REV_I: "mV",
            E_REV_I2: "mV"
        }

        self._n_neurons = n_neurons
        self._data = SpynnakerRangeDictionary(size=n_neurons)
        self._data[E_REV_E] = e_rev_E
        self._data[E_REV_E2] = e_rev_E2
        self._data[E_REV_I] = e_rev_I
        self._data[E_REV_I2] = e_rev_I2

    @property
    def e_rev_E(self):
        return self._data[E_REV_E]

    @e_rev_E.setter
    def e_rev_E(self, e_rev_E):
        self._data.set_value(key=E_REV_E, value=e_rev_E)

    @property
    def e_rev_E2(self):
        return self._data[E_REV_E2]

    @e_rev_E2.setter
    def e_rev_E2(self, e_rev_E2):
        self._data.set_value(key=E_REV_E2, value=e_rev_E2)

    @property
    def e_rev_I(self):
        return self._data[E_REV_I]

    @e_rev_I.setter
    def e_rev_I(self, e_rev_I):
        self._data.set_value(key=E_REV_I, value=e_rev_I)

    @property
    def e_rev_I2(self):
        return self._data[E_REV_I2]

    @e_rev_I2.setter
    def e_rev_I2(self, e_rev_I2):
        self._data.set_value(key=E_REV_I2, value=e_rev_I2)

    def get_global_weight_scale(self):
        return 1024.0

    def get_n_input_type_parameters(self):
        return 4

    def get_input_type_parameters(self):
        return [
            NeuronParameter(
                self._data[E_REV_E], _2E2I_CONDUCTANTCE_TYPES.E_REV_E.data_type),
            NeuronParameter(
                self._data[E_REV_E2], _2E2I_CONDUCTANTCE_TYPES.E_REV_E2.data_type),
            NeuronParameter(
                self._data[E_REV_I], _2E2I_CONDUCTANTCE_TYPES.E_REV_I.data_type),
            NeuronParameter(
                self._data[E_REV_I2], _2E2I_CONDUCTANTCE_TYPES.E_REV_I2.data_type)
        ]

    def get_input_type_parameter_types(self):
        return [item.data_type for item in _2E2I_CONDUCTANTCE_TYPES]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        return 10

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
