from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.abstract_models.abstract_contains_units import \
    AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties.neural_parameter \
    import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models.abstract_neuron_model \
    import AbstractNeuronModel
from spynnaker.pyNN.utilities import utility_calls

from data_specification.enums.data_type import DataType

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
        self._v_init = utility_calls.convert_param_to_numpy(v_init, n_neurons)
        self._v_rest = utility_calls.convert_param_to_numpy(v_rest, n_neurons)
        self._tau_m = utility_calls.convert_param_to_numpy(tau_m, n_neurons)
        self._cm = utility_calls.convert_param_to_numpy(cm, n_neurons)
        self._i_offset = utility_calls.convert_param_to_numpy(
            i_offset, n_neurons)

        if v_init is None:
            self._v_init = self._v_rest

    def initialize_v(self, v_init):
        self._v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)

    @property
    def v_init(self):
        return self._v_init

    @v_init.setter
    def v_init(self, v_init):
        self._v_init = utility_calls.convert_param_to_numpy(
            v_init, self._n_neurons)

    @property
    def v_rest(self):
        return self._v_rest

    @v_rest.setter
    def v_rest(self, v_rest):
        self._v_rest = utility_calls.convert_param_to_numpy(
            v_rest, self._n_neurons)

    @property
    def tau_m(self):
        return self._tau_m

    @tau_m.setter
    def tau_m(self, tau_m):
        self._tau_m = utility_calls.convert_param_to_numpy(
            tau_m, self._n_neurons)

    @property
    def cm(self):
        return self._cm

    @cm.setter
    def cm(self, cm):
        self._cm = utility_calls.convert_param_to_numpy(cm, self._n_neurons)

    @property
    def i_offset(self):
        return self._i_offset

    @i_offset.setter
    def i_offset(self, i_offset):
        self._i_offset = utility_calls.convert_param_to_numpy(
            i_offset, self._n_neurons)

    @property
    def _r_membrane(self):
        return self._tau_m / self._cm

    def _exp_tc(self, machine_time_step):
        return numpy.exp(float(-machine_time_step) /
                         (1000.0 * self._tau_m))

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
            NeuronParameter(self._v_init, _IF_TYPES.V_INIT.data_type),

            # membrane resting voltage [mV]
            # REAL     V_rest;
            NeuronParameter(self._v_rest, _IF_TYPES.V_REST.data_type),

            # membrane resistance [MOhm]
            # REAL     R_membrane;
            NeuronParameter(self._r_membrane, _IF_TYPES.R_MEMBRANE.data_type),

            # 'fixed' computation parameter - time constant multiplier for
            # closed-form solution
            # exp( -(machine time step in ms)/(R * C) ) [.]
            # REAL     exp_TC;
            NeuronParameter(
                self._exp_tc(machine_time_step), _IF_TYPES.EXP_TC.data_type),

            # offset current [nA]
            # REAL     I_offset;
            NeuronParameter(self._i_offset, _IF_TYPES.I_OFFSET.data_type)
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
