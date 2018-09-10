from spinn_utilities.overrides import overrides
from spinn_utilities.ranged.abstract_list import AbstractList
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged import SpynnakerRangeDictionary
from .abstract_synapse_type import AbstractSynapseType
from data_specification.enums import DataType
from spynnaker.pyNN.models.neuron.synapse_types.synapse_type_exponential \
    import get_exponential_decay_and_init

import numpy
from enum import Enum

TAU_SYN_E = 'tau_syn_E'
TAU_SYN_E2 = 'tau_syn_E2'
TAU_SYN_I = 'tau_syn_I'
TAU_SYN_I2 = 'tau_syn_I2'
GSYN_EXC = 'gsyn_exc'
GSYN_EXC_2 = 'gsyn_exc2'
GSYN_INH = 'gsyn_inh'
GSYN_INH_2 = 'gsyn_inh2'


class _2E2I_EXP_TYPES(Enum):

    E_DECAY = (1, DataType.UINT32)
    E_INIT = (2, DataType.UINT32)
    E_DECAY_2 = (3, DataType.UINT32)
    E_INIT_2 = (4, DataType.UINT32)
    I_DECAY = (5, DataType.UINT32)
    I_INIT = (6, DataType.UINT32)
    I_DECAY_2 = (7, DataType.UINT32)
    I_INIT_2 = (8, DataType.UINT32)
    INITIAL_EXC = (9, DataType.S1615)
    INITIAL_EXC_2 = (10, DataType.S1615)
    INITIAL_INH = (11, DataType.S1615)
    INITIAL_INH_2 = (12, DataType.S1615)

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


# def get_exponential_decay_and_init(tau, machine_time_step):
#     ulfract = pow(2, 32)
#     ts = float(machine_time_step) / 1000.0
#     # decay = e^(-ts / tau) as an unsigned long fract
#     decay = lambda x: int(numpy.exp(-ts / x) * ulfract)  # noqa E731
#     # init = (tau / ts) * (1 - e^(-ts / tau)) as unsigned long fract
#     init = lambda x: int((x / ts) * (1.0 - numpy.exp(-ts / x)) * ulfract)  # noqa E731,
#     if isinstance(tau, AbstractList):
#         return (
#             tau.apply_operation(decay),
#             tau.apply_operation(init))
#     # For backward compatibility in case tau is just raw collection
#     return (map(decay, tau), map(init, tau))


class SynapseTypeExponential2E2I(AbstractSynapseType, AbstractContainsUnits):
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self,
                 n_neurons,
                 tau_syn_E,
                 tau_syn_E2,
                 tau_syn_I,
                 tau_syn_I2,
                 initial_input_exc=0.0, initial_input_inh=0.0):
        # pylint: disable=too-many-arguments
        self._units = {
            TAU_SYN_E: "mV",
            TAU_SYN_E_2: "mV",
            TAU_SYN_I: 'mV',
            TAU_SYN_I_2: 'mV',
            GSYN_EXC: "uS",
            GSYN_EXC_2: "uS",
            GSYN_INH: "uS",
            GSYN_INH_2: "uS"}

        self._n_neurons = n_neurons
        self._data = SpynnakerRangeDictionary(size=n_neurons)
        self._data[TAU_SYN_E] = tau_syn_E
        self._data[TAU_SYN_E2] = tau_syn_E2
        self._data[TAU_SYN_I] = tau_syn_I
        self._data[TAU_SYN_I2] = tau_syn_I2
        self._data[GSYN_EXC] = initial_input_exc
        self._data[GSYN_EXC_2] = initial_input_exc
        self._data[GSYN_INH] = initial_input_inh
        self._data[GSYN_INH_2] = initial_input_inh

    @property
    def tau_syn_E(self):
        return self._data[TAU_SYN_E]

    @tau_syn_E.setter
    def tau_syn_E(self, tau_syn_E):
        self._data.set_value(key=TAU_SYN_E, value=tau_syn_E)

    @property
    def tau_syn_E2(self):
        return self._data[TAU_SYN_E2]

    @tau_syn_E2.setter
    def tau_syn_E2(self, tau_syn_E2):
        self._data.set_value(key=TAU_SYN_E2, value=tau_syn_E2)

    @property
    def tau_syn_I(self):
        return self._data[TAU_SYN_I]

    @tau_syn_I.setter
    def tau_syn_I(self, tau_syn_I):
        self._data.set_value(key=TAU_SYN_I, value=tau_syn_I)

    @property
    def tau_syn_I2(self):
        return self._data[TAU_SYN_I2]

    @tau_syn_I2.setter
    def tau_syn_I2(self, tau_syn_I2):
        self._data.set_value(key=TAU_SYN_I2, value=tau_syn_I2)

    @property
    def isyn_exc(self):
        return self._data[GSYN_EXC]

    @isyn_exc.setter
    def isyn_exc(self, new_value):
        self._data.set_value(key=GSYN_EXC, value=new_value)

    @property
    def isyn_exc_2(self):
        return self._data[GSYN_EXC_2]

    @isyn_exc_2.setter
    def isyn_exc_2(self, new_value):
        self._data.set_value(key=GSYN_EXC_2, value=new_value)

    @property
    def isyn_inh(self):
        return self._data[GSYN_INH]

    @isyn_inh.setter
    def isyn_inh(self, new_value):
        self._data.set_value(key=GSYN_INH, value=new_value)

    @property
    def isyn_inh_2(self):
        return self._data[GSYN_INH_2]

    @isyn_inh_2.setter
    def isyn_inh_2(self, new_value):
        self._data.set_value(key=GSYN_INH_2, value=new_value)

    @overrides(AbstractSynapseType.get_n_synapse_types)
    def get_n_synapse_types(self):
        return 4

    @overrides(AbstractSynapseType.get_synapse_id_by_target)
    def get_synapse_id_by_target(self, target):
        if target == "excitatory":
            return 0
        elif target == "excitatory2":
            return 1
        elif target == "inhibitory":
            return 2
        elif target == "inhibitory2":
            return 3
        return None

    @overrides(AbstractSynapseType.get_synapse_targets)
    def get_synapse_targets(self):
        return "excitatory", "excitatory2", "inhibitory", "inhibitory2"

    @overrides(AbstractSynapseType.get_n_synapse_type_parameters)
    def get_n_synapse_type_parameters(self):
        return 12

    @inject_items({"machine_time_step": "MachineTimeStep"})
    def get_synapse_type_parameters(self, machine_time_step):
        # pylint: disable=arguments-differ
        e_decay, e_init = get_exponential_decay_and_init(
            self._data[TAU_SYN_E], machine_time_step)
        e_decay_2, e_init_2 = get_exponential_decay_and_init(
            self._data[TAU_SYN_E2], machine_time_step)
        i_decay, i_init = get_exponential_decay_and_init(
            self._data[TAU_SYN_I], machine_time_step)
        i_decay_2, i_init_2 = get_exponential_decay_and_init(
            self._data[TAU_SYN_I2], machine_time_step)

        return [
            # Shaping parameters
            NeuronParameter(e_decay, _EXP_TYPES.E_DECAY.data_type),
            NeuronParameter(e_init, _EXP_TYPES.E_INIT.data_type),
            NeuronParameter(e_decay_2, _EXP_TYPES.E_DECAY_2.data_type),
            NeuronParameter(e_init_2, _EXP_TYPES.E_INIT_2.data_type),
            NeuronParameter(i_decay, _EXP_TYPES.I_DECAY.data_type),
            NeuronParameter(i_init, _EXP_TYPES.I_INIT.data_type),
            NeuronParameter(i_decay_2, _EXP_TYPES.I_DECAY_2.data_type),
            NeuronParameter(i_init_2, _EXP_TYPES.I_INIT_2.data_type),
            # Initialisation parameters
            NeuronParameter(
                self._data[GSYN_EXC], _EXP_TYPES.INITIAL_EXC.data_type),
            NeuronParameter(
                self._data[GSYN_EXC_2], _EXP_TYPES.INITIAL_EXC_2.data_type),
            NeuronParameter(
                self._data[GSYN_INH], _EXP_TYPES.INITIAL_INH.data_type),
            NeuronParameter(
                self._data[GSYN_INH_2], _EXP_TYPES.INITIAL_INH_2.data_type)
        ]

    @overrides(AbstractSynapseType.get_synapse_type_parameter_types)
    def get_synapse_type_parameter_types(self):
        return [item.data_type for item in _2E2I_EXP_TYPES]

    @overrides(AbstractSynapseType.get_n_cpu_cycles_per_neuron)
    def get_n_cpu_cycles_per_neuron(self):
        return 100

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
