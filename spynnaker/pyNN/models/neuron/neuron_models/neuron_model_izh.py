from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.utilities.ranged.spynakker_ranged_dict import \
    SpynakkerRangeDictionary
from .abstract_neuron_model import AbstractNeuronModel
from data_specification.enums import DataType

from enum import Enum

A = 'a'
B = 'b'
C = 'c'
D = 'd'
V_INIT = 'v_init'
U_INIT = 'u_init'
I_OFFSET = 'i_offset'


class _IZH_TYPES(Enum):
    A = (1, DataType.S1615)
    B = (2, DataType.S1615)
    C = (3, DataType.S1615)
    D = (4, DataType.S1615)
    V_INIT = (5, DataType.S1615)
    U_INIT = (6, DataType.S1615)
    I_OFFSET = (7, DataType.S1615)
    THIS_H = (8, DataType.S1615)

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


class _IZH_GLOBAL_TYPES(Enum):
    TIMESTEP = (1, DataType.S1615)

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


class NeuronModelIzh(AbstractNeuronModel, AbstractContainsUnits):
    __slots__ = [
        "_data",
        "_n_neurons",
        "_units"]

    def __init__(self, n_neurons, a, b, c, d, v_init, u_init, i_offset):
        AbstractNeuronModel.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._units = {
            A: "ms",
            B: "ms",
            C: "mV",
            D: "mV/ms",
            V_INIT: "mV",
            U_INIT: "mV/ms",
            I_OFFSET: "nA"}

        self._n_neurons = n_neurons
        self._data = SpynakkerRangeDictionary(size=n_neurons)
        self._data[A] = a
        self._data[B] = b
        self._data[C] = c
        self._data[D] = d
        self._data[V_INIT] = v_init
        self._data[U_INIT] = u_init
        self._data[I_OFFSET] = i_offset

    @property
    def a(self):
        return self._data[A]

    @a.setter
    def a(self, a):
        self._data.set_value(key=A, value=a)

    @property
    def b(self):
        return self._data[B]

    @b.setter
    def b(self, b):
        self._data.set_value(key=B, value=b)

    @property
    def c(self):
        return self._data[C]

    @c.setter
    def c(self, c):
        self._data.set_value(key=C, value=c)

    @property
    def d(self):
        return self._data[D]

    @d.setter
    def d(self, d):
        self._data.set_value(key=D, value=d)

    @property
    def i_offset(self):
        return self._data[I_OFFSET]

    @i_offset.setter
    def i_offset(self, i_offset):
        self._data.set_value(key=I_OFFSET, value=i_offset)

    @property
    def v_init(self):
        return self._data[V_INIT]

    @v_init.setter
    def v_init(self, v_init):
        self._data.set_value(key=V_INIT, value=v_init)

    @property
    def u_init(self):
        return self._data[U_INIT]

    @u_init.setter
    def u_init(self, u_init):
        self._data.set_value(key=U_INIT, value=u_init)

    def initialize_v(self, v_init):
        self._data.set_value(key=V_INIT, value=v_init)

    def initialize_u(self, u_init):
        self._data.set_value(key=U_INIT, value=u_init)

    @overrides(AbstractNeuronModel.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return 8

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_neural_parameters,
               additional_arguments={'machine_time_step'})
    def get_neural_parameters(self, machine_time_step):
        return [

            # REAL A
            NeuronParameter(self._data[A], _IZH_TYPES.A.data_type),

            # REAL B
            NeuronParameter(self._data[B], _IZH_TYPES.B.data_type),

            # REAL C
            NeuronParameter(self._data[C], _IZH_TYPES.C.data_type),

            # REAL D
            NeuronParameter(self._data[D], _IZH_TYPES.D.data_type),

            # REAL V
            NeuronParameter(self._data[V_INIT], _IZH_TYPES.V_INIT.data_type),

            # REAL U
            NeuronParameter(self._data[U_INIT], _IZH_TYPES.U_INIT.data_type),

            # offset current [nA]
            # REAL I_offset;
            NeuronParameter(self._data[I_OFFSET],
                            _IZH_TYPES.I_OFFSET.data_type),

            # current timestep - simple correction for threshold
            # REAL this_h;
            NeuronParameter(
                machine_time_step / 1000.0, _IZH_TYPES.THIS_H.data_type)
        ]

    @overrides(AbstractNeuronModel.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        return [item.data_type for item in _IZH_TYPES]

    @overrides(AbstractNeuronModel.get_n_global_parameters)
    def get_n_global_parameters(self):
        return 1

    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(AbstractNeuronModel.get_global_parameters,
               additional_arguments={'machine_time_step'})
    def get_global_parameters(self, machine_time_step):
        return [
            NeuronParameter(
                machine_time_step / 1000.0,
                _IZH_GLOBAL_TYPES.TIMESTEP.data_type)
        ]

    @overrides(AbstractNeuronModel.get_global_parameter_types)
    def get_global_parameter_types(self):
        return [item.data_type for item in _IZH_GLOBAL_TYPES]

    @overrides(AbstractNeuronModel.set_neural_parameters)
    def set_neural_parameters(self, neural_parameters, vertex_slice):
        self._v_init[vertex_slice.as_slice] = neural_parameters[4]
        self._u_init[vertex_slice.as_slice] = neural_parameters[5]

    def get_n_cpu_cycles_per_neuron(self):

        # A bit of a guess
        return 150

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return self._units[variable]
