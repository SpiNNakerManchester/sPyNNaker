from .abstract_formation import AbstractFormation
from pacman.model.decorators.overrides import overrides


class DistanceDependentFormation(AbstractFormation):
    """ Formation rule that depends on the physical distance between neurons
    """

    __slots__ = []

    @overrides(AbstractFormation.is_same_as)
    def is_same_as(self, other):
        return isinstance(other, DistanceDependentFormation)

    @property
    @overrides(AbstractFormation.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_distance"

    @overrides(AbstractFormation.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 0

    @overrides(AbstractFormation.write_parameters)
    def write_parameters(self, spec):
        pass

    @overrides(AbstractFormation.get_parameter_names)
    def get_parameter_names(self):
        return []
