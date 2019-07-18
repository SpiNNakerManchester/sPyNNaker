from .abstract_partner_selection import AbstractPartnerSelection
from pacman.model.decorators.overrides import overrides


class LastNeuronSelection(AbstractPartnerSelection):
    """ Partner selection that picks a random source neuron from the neurons\
        that spiked in the last timestep
    """

    __slots__ = ["__spike_buffer_size"]

    def __init__(self, spike_buffer_size=64):
        """

        :param spike_buffer_size: The size of the buffer for holding spikes
        """
        self.__spike_buffer_size = spike_buffer_size

    @overrides(AbstractPartnerSelection.is_same_as)
    def is_same_as(self, other):
        return isinstance(other, LastNeuronSelection)

    @property
    @overrides(AbstractPartnerSelection.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_last_neuron"

    @overrides(AbstractPartnerSelection.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 4

    @overrides(AbstractPartnerSelection.write_parameters)
    def write_parameters(self, spec):
        spec.write_value(self.__spike_buffer_size)

    @overrides(AbstractPartnerSelection.get_parameter_names)
    def get_parameter_names(self):
        return ["spike_buffer_size"]
