from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType

import numpy
from enum import Enum


class _MASS_TYPES(Enum):
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

        self._du_th = utility_calls.convert_param_to_numpy(du_th, n_neurons)
        self._tau_th = utility_calls.convert_param_to_numpy(tau_th, n_neurons)
        self._v_thresh = utility_calls.convert_param_to_numpy(
            v_thresh, n_neurons)

    @property
    def v_thresh(self):
        return self._v_thresh

    @v_thresh.setter
    def v_thresh(self, v_thresh):
        self._v_thresh = utility_calls.convert_param_to_numpy(
            v_thresh, self._n_neurons)

    @property
    def du_th(self):
        return self._du_th

    @du_th.setter
    def du_th(self, du_th):
        self._du_th = utility_calls.convert_param_to_numpy(
            du_th, self._n_neurons)

    @property
    def tau_th(self):
        return self._tau_th

    @tau_th.setter
    def tau_th(self, tau_th):
        self._tau_th = utility_calls.convert_param_to_numpy(
            tau_th, self._n_neurons)

    @property
    def _du_th_inv(self):
        return numpy.divide(1.0, self._du_th)

    @property
    def _tau_th_inv(self):
        return numpy.divide(1.0, self._tau_th)

    def get_n_threshold_parameters(self):
        return 3

    def get_threshold_parameters(self):
        return [
            NeuronParameter(self._du_th_inv, _MASS_TYPES.DU_TH.data_type),
            NeuronParameter(self._tau_th_inv, _MASS_TYPES.TAU_TH.data_type),
            NeuronParameter(self._v_thresh, _MASS_TYPES.V_THRESH.data_type)
        ]

    def get_threshold_parameter_types(self):
        return [item.data_type for item in _MASS_TYPES]

    def get_n_cpu_cycles_per_neuron(self):
        return 30
