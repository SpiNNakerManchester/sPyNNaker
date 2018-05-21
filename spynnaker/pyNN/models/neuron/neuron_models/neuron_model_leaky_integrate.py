from spinn_utilities.overrides import overrides
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
from .abstract_neuron_model import AbstractNeuronModel

from data_specification.enums import DataType

import numpy
from enum import Enum

V_INIT = "v_init"
V_REST = "v_rest"
TAU_M = "tau_m"
CM = "cm"
I_OFFSET = "i_offset"
R_MEMBRANE = "r_membrane"


class _IF_TYPES(Enum):

    V_INIT = (1, DataType.S1615)
    V_REST = (2, DataType.S1615)
    R_MEMBRANE = (3, DataType.S1615)
    EXP_TC = (4, DataType.S1615)
    I_OFFSET = (5, DataType.S1615)

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


class NeuronModelLeakyIntegrate(AbstractNeuronModel, AbstractContainsUnits):
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self, n_neurons, v_init, v_rest, tau_m, cm, i_offset):
        # pylint: disable=too-many-arguments
        self._units = {
            V_INIT: 'mV',
            V_REST: 'mV',
            TAU_M: 'ms',
            CM: 'nF',
            I_OFFSET: 'nA'}

        self._n_neurons = n_neurons
        if v_init is None:
            v_init = v_rest
        self._data = SpynnakerRangeDictionary(size=n_neurons)
        self._data[V_INIT] = v_init
        self._data[V_REST] = v_rest
        self._data[TAU_M] = tau_m
        self._data[CM] = cm
        self._data[I_OFFSET] = i_offset
        self._data["r_membrane"] = self._data[TAU_M] / self._data[CM]

    def initialize_v(self, v_init):
        self._data.set_value(key=V_INIT, value=v_init)

    @property
    def v_init(self):
        return self._data[V_INIT]

    @v_init.setter
    def v_init(self, v_init):
        self._data.set_value(key=V_INIT, value=v_init)

    @property
    def v_rest(self):
        return self._data[V_REST]

    @v_rest.setter
    def v_rest(self, v_rest):
        self._data.set_value(key=V_REST, value=v_rest)

    @property
    def tau_m(self):
        return self._data[TAU_M]

    @tau_m.setter
    def tau_m(self, tau_m):
        self._data.set_value(key=TAU_M, value=tau_m)

    @property
    def cm(self):
        return self._data[CM]

    @cm.setter
    def cm(self, cm):
        self._data.set_value(key=CM, value=cm)

    @property
    def i_offset(self):
        return self._data[I_OFFSET]

    @i_offset.setter
    def i_offset(self, i_offset):
        self._data.set_value(key=I_OFFSET, value=i_offset)

    @property
    def _r_membrane(self):
        return self._data[R_MEMBRANE]

    def _exp_tc(self, machine_time_step):
        return self._data[TAU_M].apply_operation(
            operation=lambda x: numpy.exp(
                float(-machine_time_step) / (1000.0 * x)))

    @overrides(AbstractNeuronModel.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return 5

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_neural_parameters,
               additional_arguments={'machine_time_step'})
    def get_neural_parameters(self, machine_time_step):
        # pylint: disable=arguments-differ
        return [

            # membrane voltage [mV]
            # REAL     V_membrane;
            NeuronParameter(self._data[V_INIT], _IF_TYPES.V_INIT.data_type),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._data[V_REST], _IF_TYPES.V_REST.data_type),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._data[R_MEMBRANE],
                            _IF_TYPES.R_MEMBRANE.data_type),

            # 'fixed' computation parameter - time constant multiplier for
            # closed-form solution
            # exp( -(machine time step in ms)/(R * C) ) [.]
            # REAL     exp_TC;
            NeuronParameter(
                self._exp_tc(machine_time_step),
                _IF_TYPES.EXP_TC.data_type),

            # offset current [nA]
            # REAL     I_offset;
            NeuronParameter(self._data[I_OFFSET],
                            _IF_TYPES.I_OFFSET.data_type)
        ]

    @overrides(AbstractNeuronModel.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        return [item.data_type for item in _IF_TYPES]

    @overrides(AbstractNeuronModel.get_n_global_parameters)
    def get_n_global_parameters(self):
        return 0

    @overrides(AbstractNeuronModel.get_global_parameters)
    def get_global_parameters(self):
        return []

    @overrides(AbstractNeuronModel.get_global_parameter_types)
    def get_global_parameter_types(self):
        return []

    @overrides(AbstractNeuronModel.set_neural_parameters)
    def set_neural_parameters(self, neural_parameters, vertex_slice):
        self._data[V_INIT][vertex_slice.as_slice] = neural_parameters[0]

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 80

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
