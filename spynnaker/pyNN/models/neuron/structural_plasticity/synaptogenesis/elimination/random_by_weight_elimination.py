from .abstract_elimination import AbstractElimination
from pacman.model.decorators.overrides import overrides


class RandomByWeightElimination(AbstractElimination):
    """ Elimination Rule that depends on the weight of a synapse
    """

    __slots__ = []

    @overrides(AbstractElimination.is_same_as)
    def is_same_as(self, other):
        return isinstance(other, RandomByWeightElimination)

    @property
    @overrides(AbstractElimination.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_weight"

    @overrides(AbstractElimination.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 0

    @overrides(AbstractElimination.write_parameters)
    def write_parameters(self, spec):
        pass

    @overrides(AbstractElimination.get_parameter_names)
    def get_parameter_names(self):
        return []
