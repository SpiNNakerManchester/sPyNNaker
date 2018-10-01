from data_specification.enums import DataType
from spinn_utilities.overrides import overrides
from .abstract_input_type import AbstractInputType

E_REV_E = "e_rev_E"
E_REV_E2 = "e_rev_E2"
E_REV_I = "e_rev_I"
E_REV_I2 = "e_rev_I2"

UNITS = {
    E_REV_E: "mV",
    E_REV_E2: "mV",
    E_REV_I: "mV",
    E_REV_I2: "mV"
}


class InputTypeConductance2E2I(AbstractInputType):
    """ The conductance input type
    """
    __slots__ = [
        "_e_rev_E",
        "_e_rev_E2",
        "_e_rev_I",
        "_e_rev_I2"
        ]

    def __init__(self, e_rev_E, e_rev_E2, e_rev_I, e_rev_I2):
        super(InputTypeConductance2E2I, self).__init__([
            DataType.S1615,   # e_rev_E
            DataType.S1615,   # e_rev_E2
            DataType.S1615,   # e_rev_I
            DataType.S1615])  # e_rev_I2
        self._e_rev_E = e_rev_E
        self._e_rev_E2 = e_rev_E2
        self._e_rev_I = e_rev_I
        self._e_rev_I2 = e_rev_I2

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 10 * n_neurons

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[E_REV_E] = self._e_rev_E
        parameters[E_REV_E2] = self._e_rev_E2
        parameters[E_REV_I] = self._e_rev_I
        parameters[E_REV_I2] = self._e_rev_I2

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        return [parameters[E_REV_E],
                parameters[E_REV_E2],
                parameters[E_REV_I],
                parameters[E_REV_I2]
                ]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_e_rev_E, _e_rev_E2, _e_rev_I, _e_rev_I2) = values

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1024.0

    @property
    def e_rev_E(self):
        return self._e_rev_E

    @e_rev_E.setter
    def e_rev_E(self, e_rev_E):
        self._e_rev_E = e_rev_E

    @property
    def e_rev_E2(self):
        return self._e_rev_E2

    @e_rev_E2.setter
    def e_rev_E2(self, e_rev_E2):
        self._e_rev_E2 = e_rev_E2

    @property
    def e_rev_I(self):
        return self._e_rev_I

    @e_rev_I.setter
    def e_rev_I(self, e_rev_I):
        self._e_rev_I = e_rev_I

    @property
    def e_rev_I2(self):
        return self._e_rev_I2

    @e_rev_I2.setter
    def e_rev_I2(self, e_rev_I2):
        self._e_rev_I2 = e_rev_I2

