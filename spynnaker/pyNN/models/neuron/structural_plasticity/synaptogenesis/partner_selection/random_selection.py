from .abstract_partner_selection import AbstractPartnerSelection
from pacman.model.decorators.overrides import overrides


class RandomSelection(AbstractPartnerSelection):
    """ Partner selection that picks a random source neuron from all sources
    """

    __slots__ = []

    @property
    @overrides(AbstractPartnerSelection.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_random"

    @overrides(AbstractPartnerSelection.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 0

    @overrides(AbstractPartnerSelection.write_parameters)
    def write_parameters(self, spec):
        pass

    @overrides(AbstractPartnerSelection.get_parameter_names)
    def get_parameter_names(self):
        return []
