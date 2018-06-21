from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .abstract_neuron_model import AbstractNeuronModel
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
from data_specification.enums import DataType

import numpy
from enum import Enum

V_INIT = "v_init"
G_NA = "g_Na"
E_NA = "E_Na"
G_K = "g_K"
E_K = "E_K"
TAU_M = "tau_m"
I_OFFSET = "i_offset"

_CPU_CYCLES = 70


class _HT_TYPES(Enum):
    V_INIT = (1, DataType.S1615)
    G_NA = (2, DataType.S1615)
    E_NA = (3, DataType.S1615)
    G_K = (4, DataType.S1615)
    E_K = (5, DataType.S1615)
    EXP_TC = (6, DataType.S1615)
    I_OFFSET = (7, DataType.S1615)

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


class NeuronModelHT(AbstractNeuronModel, AbstractContainsUnits):
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(
            self, n_neurons,
            v_init,
            g_Na, E_rev_Na,
            g_K, E_rev_K,
            tau_m, i_offset):

        # pylint: disable=too-many-arguments
        self._data = SpynnakerRangeDictionary(size=n_neurons)
        self._data[V_INIT] = v_init,
        self._data[G_NA] = g_Na
        self._data[E_NA] = E_rev_Na
        self._data[G_K] = g_K
        self._data[E_K] = E_rev_K
        self._data[TAU_M] = tau_m
        self._data[I_OFFSET] = i_offset
        self._units = {
            V_INIT: 'mV',
            G_NA: 'microS',
            E_NA: 'mV',
            G_K: 'microS',
            E_K: 'mV',
            TAU_M: 'ms',
            I_OFFSET: 'nA'}

    @property
    def v_init(self):
        return self._data[V_INIT]

    @v_init.setter
    def v_init(self, v_init):
        self._data.set_value(key=V_INIT, value=v_init)

    @property
    def g_Na(self):
        return self._data[G_NA]

    @g_Na.setter
    def g_Na(self, g_Na):
        self._data.set_value(key=G_NA, value=g_Na)

    @property
    def E_Na(self):
        return self._data[E_NA]

    @E_Na.setter
    def E_Na(self, E_Na):
        self._data.set_value(key=E_NA, value=E_Na)

    @property
    def g_K(self):
        return self._data[G_K]

    @g_K.setter
    def g_K(self, g_K):
        self._data.set_value(key=G_K, value=g_K)

    @property
    def E_K(self):
        return self._data[E_K]

    @E_K.setter
    def E_K(self, E_rev_K):
        self._data.set_value(key=E_K, value=E_rev_K)

    @property
    def tau_m(self):
        return self._data[TAU_M]

    @tau_m.setter
    def tau_m(self, tau_m):
        self._data.set_value(key=TAU_M, value=tau_m)

    @property
    def i_offset(self):
        return self._data[I_OFFSET]

    @i_offset.setter
    def tau_m(self, i_offset):
        self._data.set_value(key=I_OFFSET, value=i_offset)


    @overrides(AbstractNeuronModel.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return 7

    def _exp_tc(self, machine_time_step):
        return self._data[TAU_M].apply_operation(
            operation=lambda x: numpy.exp(
                float(-machine_time_step) / (1000.0 * x)))

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_neural_parameters,
               additional_arguments={'machine_time_step'})
    def get_neural_parameters(self, machine_time_step):
        params =  []
        params.extend([

            NeuronParameter(
                self._data[V_INIT],
                _HT_TYPES.V_INIT.data_type),

            NeuronParameter(
                self._data[G_NA],
                _HT_TYPES.G_NA.data_type),

            NeuronParameter(
                self._data[E_NA],
                _HT_TYPES.E_NA.data_type),

            NeuronParameter(
                self._data[G_K],
                _HT_TYPES.G_K.data_type),

            NeuronParameter(
                self._data[E_K],
                _HT_TYPES.E_K.data_type),

            NeuronParameter(
                self._exp_tc(machine_time_step),
                _HT_TYPES.EXP_TC.data_type),

            NeuronParameter(
                self._data[I_OFFSET],
                _HT_TYPES.I_OFFSET.data_type),
        ])
        return params

    @overrides(AbstractNeuronModel.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        return [item.data_type for item in _HT_TYPES]

    @overrides(AbstractNeuronModel.get_n_global_parameters)
    def get_n_global_parameters(self):
        return 0

    @overrides(AbstractNeuronModel.get_global_parameter_types)
    def get_global_parameter_types(self):
        return []

    @overrides(AbstractNeuronModel.get_global_parameters)
    def get_global_parameters(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):
        return _CPU_CYCLES

    @overrides(AbstractNeuronModel.set_neural_parameters)
    def set_neural_parameters(self, neural_parameters, vertex_slice):
        self._data[V_INIT][vertex_slice.as_slice] = neural_parameters[0]

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]

