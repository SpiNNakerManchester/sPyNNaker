from spinn_utilities.overrides import overrides
from .abstract_input_type import AbstractInputType
import numpy


class InputTypeCurrent(AbstractInputType):
    """ The current input type
    """
    __slots__ = []

    @overrides(AbstractInputType.get_n_cpu_cycles)
    def get_n_cpu_cycles(self, n_neurons):
        return 0

    @overrides(AbstractInputType.get_dtcm_usage_in_bytes)
    def get_dtcm_usage_in_bytes(self, n_neurons):
        return 0

    @overrides(AbstractInputType.get_sdram_usage_in_bytes)
    def get_sdram_usage_in_bytes(self, n_neurons):
        return 0

    @overrides(AbstractInputType.add_parameters)
    def add_parameters(self, parameters):
        pass

    @overrides(AbstractInputType.add_state_variables)
    def add_state_variables(self, state_variables):
        pass

    @overrides(AbstractInputType.get_data)
    def get_data(self, parameters, state_variables, vertex_slice):
        return numpy.zeros(0, dtype="uint32")

    @overrides(AbstractInputType.read_data)
    def read_data(
            self, data, offset, vertex_slice, parameters, state_variables):
        return offset

    @overrides(AbstractInputType.get_units)
    def get_units(self, variable):
        raise KeyError(variable)

    @overrides(AbstractInputType.has_variable)
    def has_variable(self, variable):
        return False

    @overrides(AbstractInputType.get_global_weight_scale)
    def get_global_weight_scale(self):
        return 1.0
