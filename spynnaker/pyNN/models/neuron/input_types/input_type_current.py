from spinn_utilities.overrides import overrides
from .abstract_input_type import AbstractInputType


class InputTypeCurrent(AbstractInputType):
    """ The current input type
    """
    __slots__ = []

    def __init__(self):
        super(InputTypeCurrent, self).__init__([])

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 0

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        pass

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_values)
    def get_values(self, parameters, state_variables):
        return []

    @overrides(AbstractInputType.read_data)
    def update_values(self, values, parameters, state_variables):
        pass

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        raise KeyError(variable)

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return False

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1.0
