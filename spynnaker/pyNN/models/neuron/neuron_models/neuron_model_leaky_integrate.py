from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from .abstract_neuron_model import AbstractNeuronModel

from data_specification.enums import DataType
from spinn_utilities.ranged.range_dictionary import RangeDictionary

import numpy
from enum import Enum


class _IF_TYPES(Enum):

    V_INIT = (1, DataType.S1615)
    V_REST = (2, DataType.S1615)
    R_MEMBRANE = (3, DataType.S1615)
    EXP_TC = (4, DataType.S1615)
    I_OFFSET = (5, DataType.S1615)

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class NeuronModelLeakyIntegrate(AbstractNeuronModel, AbstractContainsUnits):

    def __init__(self, n_neurons, v_init, v_rest, tau_m, cm, i_offset):
        AbstractNeuronModel.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            'v_init': 'mV',
            'v_rest': 'mV',
            'tau_m': 'ms',
            'cm': 'nF',
            'i_offset': 'nA'}

        self._n_neurons = n_neurons
        if v_init is None:
            v_init = v_rest
        defaults = {}
        defaults["v_init"] = v_init
        defaults["v_rest"] = v_rest
        defaults["tau_m"] = tau_m
        defaults["cm"] = cm
        defaults["i_offset"] = i_offset
        self._data = RangeDictionary(size=n_neurons, defaults=defaults)
        r_membrane = self._data.get_list("tau_m") / self._data.get_list("cm")
        self._data.add_list("r_membrane", r_membrane)

    def initialize_v(self, v_init):
        self._data.set_value(key="v_init", value=v_init)

    @property
    def v_init(self):
        return self._data.get_list("v_init")

    @v_init.setter
    def v_init(self, v_init):
        self._data.set_value(key="v_init", value=v_init)

    @property
    def v_rest(self):
        return self._data.get_list("v_rest")

    @v_rest.setter
    def v_rest(self, v_rest):
        self._data.set_value(key="v_rest", value=v_rest)

    @property
    def tau_m(self):
        return self._data.get_list("tau_m")

    @tau_m.setter
    def tau_m(self, tau_m):
        self._data.set_value(key="tau_m", value=tau_m)

    @property
    def cm(self):
        return self._data.get_list("cm")

    @cm.setter
    def cm(self, cm):
        self._data.set_value(key="cm", value=cm)

    @property
    def i_offset(self):
        return self._data.get_list("i_offset")

    @i_offset.setter
    def i_offset(self, i_offset):
        self._data.set_value(key="i_offset", value=i_offset)

    @property
    def _r_membrane(self):
        return self._data.get_list("r_membrane")

    def _exp_tc(self, machine_time_step):
        operation = lambda x: numpy.exp(float(-machine_time_step) /
                                        (1000.0 * x))
        return self._data.get_list("tau_m")\
            .apply_operation(operation=operation)

    @overrides(AbstractNeuronModel.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return 5

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_neural_parameters,
               additional_arguments={'machine_time_step'})
    def get_neural_parameters(self, machine_time_step):
        return [

            # membrane voltage [mV]
            # REAL     V_membrane;
            NeuronParameter(self._data.get_list("v_init"),
                            _IF_TYPES.V_INIT.data_type),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._data.get_list("v_rest"),
                            _IF_TYPES.V_REST.data_type),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._data.get_list("r_membrane"),
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
            NeuronParameter(self._data.get_list("i_offset"),
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
        self._v_init[vertex_slice.as_slice] = neural_parameters[0]

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 80

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
