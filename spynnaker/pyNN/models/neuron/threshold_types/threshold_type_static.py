from pacman.model.decorators import overrides

from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
    SpynakkerRangeDictionary
from .abstract_threshold_type import AbstractThresholdType

from data_specification.enums import DataType

from enum import Enum

V_THRESH = "v_thresh"


class _STATIC_TYPES(Enum):
    V_THRESH = (1, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class ThresholdTypeStatic(AbstractThresholdType, AbstractContainsUnits):

    """ A threshold that is a static value
    """

    def __init__(self, n_neurons, v_thresh):
        AbstractThresholdType.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {V_THRESH: "mV"}

        self._n_neurons = n_neurons
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[V_THRESH] = v_thresh

    @property
    def v_thresh(self):
        return self._data[V_THRESH]

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._data.set_value(key=V_THRESH, value=v_thresh)

    @overrides(AbstractThresholdType.get_n_threshold_parameters)
    def get_n_threshold_parameters(self):
        return 1

    @overrides(AbstractThresholdType.get_threshold_parameters)
    def get_threshold_parameters(self):
        return [
            NeuronParameter(self._data[V_THRESH],
                            _STATIC_TYPES.V_THRESH.data_type)
        ]

    @overrides(AbstractThresholdType.get_threshold_parameter_types)
    def get_threshold_parameter_types(self):
        return [item.data_type for item in _STATIC_TYPES]

    def get_n_cpu_cycles_per_neuron(self):

        # Just a comparison, but 2 just in case!
        return 2

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
