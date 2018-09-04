from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary

from .abstract_input_type import AbstractInputType

from enum import Enum

AMPA_REV_E = "ampa_rev_E"
NMDA_REV_E = "nmda_rev_E"
GABA_A_REV_E = "gaba_a_rev_E"
GABA_B_REV_E = "gaba_b_rev_E"


class _CONDUCTANTCE_TYPES(Enum):
    AMPA_REV_E = (1, DataType.S1615)
    NMDA_REV_E = (2, DataType.S1615)
    GABA_A_REV_E = (3, DataType.S1615)
    GABA_B_REV_E = (4, DataType.S1615)

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


class InputTypeHTConductance(AbstractInputType, AbstractContainsUnits):
    """ The conductance input type
    """
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self,
                 n_neurons,
                 ampa_rev_E,
                 nmda_rev_E,
                 gaba_a_rev_E,
                 gaba_b_rev_E
                 ):
        self._units = {
            AMPA_REV_E: "mV",
            NMDA_REV_E: "mV",
            GABA_A_REV_E: "mV",
            GABA_B_REV_E: "mV"
        }

        self._n_neurons = n_neurons
        self._data = SpynnakerRangeDictionary(size=n_neurons)
        self._data[AMPA_REV_E] = ampa_rev_E
        self._data[NMDA_REV_E] = nmda_rev_E
        self._data[GABA_A_REV_E] = gaba_a_rev_E
        self._data[GABA_B_REV_E] = gaba_b_rev_E

    @property
    def ampa_rev_E(self):
        return self._data[AMPA_REV_E]

    @ampa_rev_E.setter
    def ampa_rev_E(self, ampa_rev_E):
        self._data.set_value(key=AMPA_REV_E, value=ampa_rev_E)

    @property
    def nmda_rev_E(self):
        return self._data[NMDA_REV_E]

    @ampa_rev_E.setter
    def nmda_rev_E(self, nmda_rev_E):
        self._data.set_value(key=NMDA_REV_E, value=nmda_rev_E)

    @property
    def gaba_a_rev_E(self):
        return self._data[GABA_A_REV_E]

    @gaba_a_rev_E.setter
    def gaba_a_rev_E(self, gaba_a_rev_E):
        self._data.set_value(key=GABA_A_REV_E, value=gaba_a_rev_E)

    @property
    def gaba_b_rev_E(self):
        return self._data[GABA_A_REV_E]

    @gaba_b_rev_E.setter
    def gaba_b_rev_E(self, gaba_b_rev_E):
        self._data.set_value(key=GABA_A_REV_E, value=gaba_b_rev_E)

    def get_global_weight_scale(self):
        return 1024.0

    def get_n_input_type_parameters(self):
        return 4

    def get_input_type_parameters(self):
        return [
            NeuronParameter(
                self._data[AMPA_REV_E], _CONDUCTANTCE_TYPES.AMPA_REV_E.data_type),
            NeuronParameter(
                self._data[NMDA_REV_E], _CONDUCTANTCE_TYPES.NMDA_REV_E.data_type),
            NeuronParameter(
                self._data[GABA_A_REV_E], _CONDUCTANTCE_TYPES.GABA_A_REV_E.data_type),
            NeuronParameter(
                self._data[GABA_B_REV_E], _CONDUCTANTCE_TYPES.GABA_B_REV_E.data_type)
        ]

    def get_input_type_parameter_types(self):
        return [item.data_type for item in _CONDUCTANTCE_TYPES]

    def get_n_cpu_cycles_per_neuron(self, n_synapse_types):
        return 10

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
