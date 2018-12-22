from spinn_utilities.overrides import overrides
from .abstract_threshold_type import AbstractThresholdType
from pacman.executor.injection_decorator import inject_items
from data_specification.enums import DataType

import numpy

BIG_B = "big_b"
SMALL_B = "small_b"
SMALL_B_0 = "small_b_0"
TAU_A = "tau_a"
BETA = "beta"
ADPT = "adpt"

UNITS = {
         BIG_B: "mV",
         SMALL_B: "mV",
         SMALL_B_0: "mV",
         TAU_A: "ms",
         BETA: "N/A",
#          ADPT: "mV"
         }




class ThresholdTypeAdaptive(AbstractThresholdType):
    """ A threshold that is a static value
    """
    __slots__ = [
        "_v_thresh",
        "_B",
        "_small_b",
        "_small_b_0",
        "_tau_a",
        "_beta",
#         "_adpt"
        ]

    def __init__(self,  B, small_b, small_b_0, tau_a, beta):
        super(ThresholdTypeAdaptive, self).__init__([
            DataType.S1615,
            DataType.S1615,
            DataType.S1615,
            DataType.UINT32,
            DataType.S1615,
            DataType.UINT32
            ])
        self._B = B
        self._small_b = small_b
        self._small_b_0 = small_b_0
        self._tau_a = tau_a
        self._beta = beta

    @overrides(AbstractThresholdType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # Just a comparison, but 2 just in case!
        return 2 * n_neurons

    @overrides(AbstractThresholdType.add_parameters)
    def add_parameters(self, parameters):
        parameters[SMALL_B_0] = self._small_b_0
        parameters[TAU_A] = self._tau_a
        parameters[BETA] = self._beta

    @overrides(AbstractThresholdType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[BIG_B] = self._B
        state_variables[SMALL_B] = self._small_b

    @overrides(AbstractThresholdType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractThresholdType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @inject_items({"ts": "MachineTimeStep"})
    @overrides(AbstractThresholdType.get_values, additional_arguments={'ts'})
    def get_values(self, parameters, state_variables, vertex_slice, ts):

        ulfract = pow(2, 32)

        # Add the rest of the data
        return [
            state_variables[BIG_B],
            state_variables[SMALL_B],
            parameters[SMALL_B_0],
            parameters[TAU_A].apply_operation(
                    operation=lambda
                    x: numpy.exp(float(-ts) / (1000.0 * x)) * ulfract),
            parameters[BETA],
            parameters[TAU_A].apply_operation(
                operation=lambda x: (1 - numpy.exp(
                float(-ts) / (1000.0 * x))) * ulfract) # ADPT
            ]

    @overrides(AbstractThresholdType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (big_b, small_b, _small_b_0, _e_to_dt_on_tau_a, _beta, ) = values

        state_variables[BIG_B] = big_b
        state_variables[SMALL_B] = small_b

    @property
    def B(self):
        return self._B

    @B.setter
    def B(self, new_value):
        self._B = new_value

    @property
    def small_b(self):
        return self._small_b

    @small_b.setter
    def small_b(self, new_value):
        self._small_b = new_value

    @property
    def small_b_0(self):
        return self._small_b_0

    @small_b_0.setter
    def small_b_0(self, new_value):
        self._small_b_0 = new_value

    @property
    def tau_a(self):
        return self._tau_a

    @tau_a.setter
    def tau_a(self, new_value):
        self._tau_a = new_value

    @property
    def beta(self):
        return self._beta

    @beta.setter
    def beta(self, new_value):
        self._beta = new_value





# from pacman.model.decorators import overrides
#
# from pacman.executor.injection_decorator import inject_items
# from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
# from spynnaker.pyNN.models.neural_properties import NeuronParameter
# from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
#     SpynakkerRangeDictionary
# from .abstract_threshold_type import AbstractThresholdType
#
# from data_specification.enums import DataType
# import numpy
# from enum import Enum
#
# BIG_B = "B"
# SMALL_B = "small_b"
# SMALL_B_0 = "small_b_0"
# TAU_A = "tau_a"
# BETA = "beta"
# ADPT = "adpt"
#
#
# class _ADAPTIVE_TYPES(Enum):
#     BIG_B = (1, DataType.S1615) # instantaneous threshold level
#     SMALL_B = (2, DataType.S1615) # small b
#     SMALL_B_0 = (3, DataType.S1615) # baseline threshold
#     E_TO_DT_ON_TAU = (4, DataType.UINT32) # decay multiplier
#     BETA  = (5, DataType.S1615) # Adaptation on spiking
#     ADPT = (6, DataType.UINT32) # beta/tau_a
#
#     def __new__(cls, value, data_type):
#         obj = object.__new__(cls)
#         obj._value_ = value
#         obj._data_type = data_type
#         return obj
#
#     @property
#     def data_type(self):
#         return self._data_type
#
#
# class ThresholdTypeAdaptive(AbstractThresholdType, AbstractContainsUnits):
#
#     """ A threshold which increases when the neuron spikes, and decays exponentially
#         back to baseline with time
#     """
#
#     def __init__(self, n_neurons, B, small_b, small_b_0, tau_a, beta):
#         AbstractThresholdType.__init__(self)
#         AbstractContainsUnits.__init__(self)
#
#         self._units = {BIG_B: "mV",
#                        SMALL_B: "mV",
#                        SMALL_B_0: "mV",
#                        TAU_A: "ms",
#                        BETA: "NA",
#                        ADPT: "mv"}
#
#         self._n_neurons = n_neurons
#         self._data = SpynakkerRangeDictionary(size=n_neurons)
#         self._data[BIG_B] = B
#         self._data[SMALL_B] = small_b
#         self._data[SMALL_B_0] = small_b_0
#         self._data[TAU_A] = tau_a
#         self._data[BETA] = beta
#
#
#     @property
#     def B(self):
#         return self._data[BIG_B]
#
#     @B.setter
#     def B(self, B):
#         self._data.set_value(key=BIG_B, value=B)
#
#     @property
#     def b(self):
#         return self._data[SMALL_B]
#
#     @b.setter
#     def b(self, b):
#         self._data.set_value(key=SMALL_B, value=b)
#
#     @property
#     def b_0(self):
#         return self._data[SMALL_B_0]
#
#     @b_0.setter
#     def b_0(self, b_0):
#         self._data.set_value(key=SMALL_B_0, value=b_0)
#
#     @property
#     def tau_a(self):
#         return self._data[TAU_A]
#
#     @tau_a.setter
#     def tau_a(self, tau_a):
#         self._data.set_value(key=TAU_A, value=tau_a)
#
#     @property
#     def beta(self):
#         return self._data[BETA]
#
#     @beta.setter
#     def beta(self, thesh_beta):
#         self._data.set_value(key=BETA, value=beta)
#
#
#     @overrides(AbstractThresholdType.get_n_threshold_parameters)
#     def get_n_threshold_parameters(self):
#         return 6
#
#     @inject_items({"machine_timestep": "MachineTimeStep"})
#     def _exp_tau(self, machine_timestep):
#         ulfract = pow(2, 32)
#         return self._data[TAU_A].apply_operation(
#             operation=lambda x: numpy.exp(
#                 float(-machine_timestep) / (1000.0 * x)) * ulfract)
#
#     @inject_items({"machine_timestep": "MachineTimeStep"})
#     def _calc_adpt(self, machine_timestep):
#         ulfract = pow(2,32)
#         return self._data[TAU_A].apply_operation(
#             operation=lambda x: (1 - numpy.exp(
#                 float(-machine_timestep) / (1000.0 * x))) * ulfract)
#
#     @overrides(AbstractThresholdType.get_threshold_parameters)
#     def get_threshold_parameters(self):
#         return [
#             NeuronParameter(self._data[BIG_B],
#                             _ADAPTIVE_TYPES.BIG_B.data_type),
#
#             NeuronParameter(self._data[SMALL_B],
#                             _ADAPTIVE_TYPES.SMALL_B.data_type),
#
#             NeuronParameter(self._data[SMALL_B_0],
#                             _ADAPTIVE_TYPES.SMALL_B_0.data_type),
#
#             NeuronParameter(self._exp_tau(),
#                             _ADAPTIVE_TYPES.E_TO_DT_ON_TAU.data_type),
#
#             NeuronParameter(self._data[BETA],
#                             _ADAPTIVE_TYPES.BETA.data_type),
#
#             NeuronParameter(self._calc_adpt(),
#                             _ADAPTIVE_TYPES.ADPT.data_type),
#
#         ]
#
#     @overrides(AbstractThresholdType.get_threshold_parameter_types)
#     def get_threshold_parameter_types(self):
#         return [item.data_type for item in _ADAPTIVE_TYPES]
#
#     def get_n_cpu_cycles_per_neuron(self):
#         return 10
#
#     @overrides(AbstractContainsUnits.get_units)
#     def get_units(self, variable):
#         return self._units[variable]