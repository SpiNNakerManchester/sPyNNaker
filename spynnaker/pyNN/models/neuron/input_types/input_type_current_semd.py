from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from .abstract_input_type import AbstractInputType

MULTIPLICATOR = "multiplicator"
INH_INPUT_PREVIOUS = "inh_input_previous"

UNITS = {
    MULTIPLICATOR: "0",
    INH_INPUT_PREVIOUS: "mV"
}


class InputTypeCurrentSEMD(AbstractInputType):
    """ The current sEMD input type
    """
    __slots__ = [
        "__multiplicator",
        "__inh_input_previous"]

    def __init__(self, multiplicator, inh_input_previous):
        super(InputTypeCurrentSEMD, self).__init__([
            DataType.S1615,   # multiplicator
            DataType.S1615])  # inh_input_previous
        self.__multiplicator = multiplicator
        self.__inh_input_previous = inh_input_previous

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        # A bit of a guess
        return 10 * n_neurons

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        parameters[MULTIPLICATOR] = self.__multiplicator

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        state_variables[INH_INPUT_PREVIOUS] = self.__inh_input_previous

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        return UNITS[variable]

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return variable in UNITS

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables, vertex_slice):

        # Add the rest of the data
        return [parameters[MULTIPLICATOR], state_variables[INH_INPUT_PREVIOUS]]

    @overrides(AbstractInputType.update_values)
    def update_values(self, values, parameters, state_variables):

        # Read the data
        (_multiplicator, inh_input_previous) = values

        state_variables[INH_INPUT_PREVIOUS] = inh_input_previous

    @property
    def multiplicator(self):
        return self.__multiplicator

    @multiplicator.setter
    def multiplicator(self, multiplicator):
        self.__multiplicator = multiplicator

    @property
    def inh_input_previous(self):
        return self.__inh_input_previous

    @inh_input_previous.setter
    def inh_input_previous(self, inh_input_previous):
        self.__inh_input_previous = inh_input_previous

    def get_global_weight_scale(self):
        return 1.0
