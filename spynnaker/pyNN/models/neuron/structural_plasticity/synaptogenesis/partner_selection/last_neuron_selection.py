# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from spinn_utilities.overrides import overrides
from .abstract_partner_selection import AbstractPartnerSelection


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
