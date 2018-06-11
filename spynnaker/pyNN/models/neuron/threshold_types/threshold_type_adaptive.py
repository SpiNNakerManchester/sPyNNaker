from pacman.model.decorators import overrides

from pacman.executor.injection_decorator import inject_items
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
    SpynakkerRangeDictionary
from .abstract_threshold_type import AbstractThresholdType

from data_specification.enums import DataType
import numpy
from enum import Enum

BIG_B = "B"
SMALL_B = "small_b"
SMALL_B_0 = "small_b_0"
TAU_A = "tau_a"
BETA = "beta"
ADPT = "adpt"


class _ADAPTIVE_TYPES(Enum):
    BIG_B = (1, DataType.S1615) # instantaneous threshold level
    SMALL_B = (2, DataType.S1615) # small b
    SMALL_B_0 = (3, DataType.S1615) # baseline threshold
    E_TO_DT_ON_TAU = (4, DataType.UINT32) # decay multiplier
    BETA  = (5, DataType.S1615) # Adaptation on spiking
    ADPT = (6, DataType.UINT32) # beta/tau_a

    def __new__(cls, value, data_type):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data_type = data_type
        return obj

    @property
    def data_type(self):
        return self._data_type


class ThresholdTypeAdaptive(AbstractThresholdType, AbstractContainsUnits):

    """ A threshold which increases when the neuron spikes, and decays exponentially
        back to baseline with time
    """

    def __init__(self, n_neurons, B, small_b, small_b_0, tau_a, beta):
        AbstractThresholdType.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {BIG_B: "mV",
                       SMALL_B: "mV",
                       SMALL_B_0: "mV",
                       TAU_A: "ms",
                       BETA: "NA",
                       ADPT: "mv"}

        self._n_neurons = n_neurons
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[BIG_B] = B
        self._data[SMALL_B] = small_b
        self._data[SMALL_B_0] = small_b_0
        self._data[TAU_A] = tau_a
        self._data[BETA] = beta


    @property
    def thresh_B(self):
        return self._data[BIG_B]

    @thresh_B.setter
    def thresh_B(self, B):
        self._data.set_value(key=BIG_B, value=B)

    @property
    def thresh_b(self):
        return self._data[SMALL_B]

    @thresh_b.setter
    def thresh_b(self, thresh_b):
        self._data.set_value(key=SMALL_B, value=thresh_b)

    @property
    def thresh_b_0(self):
        return self._data[SMALL_B_0]

    @thresh_b_0.setter
    def thresh_b_0(self, thresh_b_0):
        self._data.set_value(key=SMALL_B_0, value=thresh_b_0)

    @property
    def thresh_tau_a(self):
        return self._data[TAU_A]

    @thresh_tau_a.setter
    def thresh_tau_a(self, thresh_tau_a):
        self._data.set_value(key=TAU_A, value=thresh_tau_a)

    @property
    def thresh_beta(self):
        return self._data[BETA]

    @thresh_beta.setter
    def thresh_beta(self, thesh_beta):
        self._data.set_value(key=BETA, value=thresh_beta)


    @overrides(AbstractThresholdType.get_n_threshold_parameters)
    def get_n_threshold_parameters(self):
        return 6

    @inject_items({"machine_timestep": "MachineTimeStep"})
    def _exp_thresh_tau(self, machine_timestep):
        ulfract = pow(2, 32)
        return self._data[TAU_A].apply_operation(
            operation=lambda x: numpy.exp(
                float(-machine_timestep) / (1000.0 * x)) * ulfract)

    @inject_items({"machine_timestep": "MachineTimeStep"})
    def _calc_adpt(self, machine_timestep):
        ulfract = pow(2,32)
        return self._data[TAU_A].apply_operation(
            operation=lambda x: (1 - numpy.exp(
                float(-machine_timestep) / (1000.0 * x))) * ulfract)

    @overrides(AbstractThresholdType.get_threshold_parameters)
    def get_threshold_parameters(self):
        return [
            NeuronParameter(self._data[BIG_B],
                            _ADAPTIVE_TYPES.BIG_B.data_type),

            NeuronParameter(self._data[SMALL_B],
                            _ADAPTIVE_TYPES.SMALL_B.data_type),

            NeuronParameter(self._data[SMALL_B_0],
                            _ADAPTIVE_TYPES.SMALL_B_0.data_type),

            NeuronParameter(self._exp_thresh_tau(),
                            _ADAPTIVE_TYPES.E_TO_DT_ON_TAU.data_type),

            NeuronParameter(self._data[BETA],
                            _ADAPTIVE_TYPES.BETA.data_type),

            NeuronParameter(self._calc_adpt(),
                            _ADAPTIVE_TYPES.ADPT.data_type),

        ]

    @overrides(AbstractThresholdType.get_threshold_parameter_types)
    def get_threshold_parameter_types(self):
        return [item.data_type for item in _ADAPTIVE_TYPES]

    def get_n_cpu_cycles_per_neuron(self):
        return 10

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]