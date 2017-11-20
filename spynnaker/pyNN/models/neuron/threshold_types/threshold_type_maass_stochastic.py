from spynnaker.pyNN.models.neural_properties import NeuronParameter
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType
from spinn_utilities.ranged.range_dictionary import RangeDictionary

import numpy
from enum import Enum

DU_TH = "du_th"
DU_TH_INV = "du_th_inv"
TAU_TH = "tau_th"
TAU_TH_INV = "tau_th_inv"
V_THRESH = "v_thresh"


class _MAASS_TYPES(Enum):
    DU_TH = (1, DataType.S1615)
    TAU_TH = (2, DataType.S1615)
    V_THRESH = (3, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class ThresholdTypeMaassStochastic(AbstractThresholdType):
    """ A stochastic threshold
    """

    def __init__(self, n_neurons, du_th, tau_th, v_thresh):
        AbstractThresholdType.__init__(self)
        self._n_neurons = n_neurons

        self._data = RangeDictionary(size=n_neurons)
        self._data[DU_TH] = du_th
        self._data[DU_TH_INV] = self._data[DU_TH].apply_operation(
            lambda x: 1.0 / x)
        self._data[TAU_TH] = tau_th
        self._data[TAU_TH_INV] = self._data[TAU_TH].apply_operation(
            lambda x: 1.0 / x)
        self._data[V_THRESH] = v_thresh

    @property
    def v_thresh(self):
        return self._data[V_THRESH]

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._data.set_value(key=V_THRESH, value=v_thresh)

    @property
    def du_th(self):
        return self._data[DU_TH]

    @du_th.setter
    def du_th(self, du_th):
        self._data.set_value(key=DU_TH, value=du_th)

    @property
    def tau_th(self):
        return self._data[TAU_TH]

    @tau_th.setter
    def tau_th(self, tau_th):
        self._data.set_value(key=TAU_TH, value=tau_th)

    @property
    def _du_th_inv(self):
        return self._data[DU_TH_INV]

    @property
    def _tau_th_inv(self):
        return self._data[TAU_TH_INV]

    def get_n_threshold_parameters(self):
        return 3

    def get_threshold_parameters(self):
        return [
            NeuronParameter(
                self._data[DU_TH_INV], _MAASS_TYPES.DU_TH.data_type),
            NeuronParameter(
                self._data[TAU_TH_INV], _MAASS_TYPES.TAU_TH.data_type),
            NeuronParameter(
                self._data[V_THRESH], _MAASS_TYPES.V_THRESH.data_type)
        ]

    def get_threshold_parameter_types(self):
        return [item.data_type for item in _MAASS_TYPES]

    def get_n_cpu_cycles_per_neuron(self):
        return 30
