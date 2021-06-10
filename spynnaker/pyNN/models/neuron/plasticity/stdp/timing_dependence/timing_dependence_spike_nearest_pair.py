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
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    get_exp_lut_array, get_min_lut_value)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)
from .abstract_timing_dependence import AbstractTimingDependence


class TimingDependenceSpikeNearestPair(AbstractTimingDependence):
    """ A timing dependence STDP rule based on nearest pairs.
    """
    __slots__ = [
        "__synapse_structure",
        "__tau_minus",
        "__tau_minus_data",
        "__tau_plus",
        "__tau_plus_data",
        "__a_plus",
        "__a_minus"]
    __PARAM_NAMES = ('tau_plus', 'tau_minus')
    default_parameters = {'tau_plus': 20.0, 'tau_minus': 20.0}

    def __init__(self, tau_plus=default_parameters['tau_plus'],
                 tau_minus=default_parameters['tau_minus'],
                 A_plus=0.01, A_minus=0.01):
        r"""
        :param float tau_plus: :math:`\tau_+`
        :param float tau_minus: :math:`\tau_-`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus
        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self.__synapse_structure = SynapseStructureWeightOnly()

        ts = machine_time_step_ms()
        self.__tau_plus_data = get_exp_lut_array(ts, self.__tau_plus)
        self.__tau_minus_data = get_exp_lut_array(ts, self.__tau_minus)

    @property
    def tau_plus(self):
        r""" :math:`\tau_+`

        :rtype: float
        """
        return self.__tau_plus

    @property
    def tau_minus(self):
        r""" :math:`\tau_-`

        :rtype: float
        """
        return self.__tau_minus

    @property
    def A_plus(self):
        r""" :math:`A^+`

        :rtype: float
        """
        return self.__a_plus

    @A_plus.setter
    def A_plus(self, new_value):
        self.__a_plus = new_value

    @property
    def A_minus(self):
        r""" :math:`A^-`

        :rtype: float
        """
        return self.__a_minus

    @A_minus.setter
    def A_minus(self, new_value):
        self.__a_minus = new_value

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        # pylint: disable=protected-access
        if not isinstance(timing_dependence, TimingDependenceSpikeNearestPair):
            return False
        return (self.__tau_plus == timing_dependence.tau_plus and
                self.__tau_minus == timing_dependence.tau_minus)

    @property
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """
        return "nearest_pair"

    @property
    def pre_trace_n_bytes(self):
        """ The number of bytes used by the pre-trace of the rule per neuron

        :rtype: int
        """
        # Pair rule requires no pre-synaptic trace when only the nearest
        # Neighbours are considered and, a single 16-bit R1 trace
        return 0

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return BYTES_PER_WORD * (len(self.__tau_plus_data) +
                                 len(self.__tau_minus_data))

    @property
    def n_weight_terms(self):
        """ The number of weight terms expected by this timing rule

        :rtype: int
        """
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, weight_scales):
        # Write lookup tables
        spec.write_array(self.__tau_plus_data)
        spec.write_array(self.__tau_minus_data)

    @property
    def synaptic_structure(self):
        """ Get the synaptic structure of the plastic part of the rows

        :rtype: AbstractSynapseStructure
        """
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return self.__PARAM_NAMES

    @overrides(AbstractTimingDependence.minimum_delta)
    def minimum_delta(self, max_stdp_spike_delta):
        ts = get_simulator().machine_time_step / 1000.0
        return [
            get_min_lut_value(self.__tau_plus_data, ts, max_stdp_spike_delta),
            get_min_lut_value(self.__tau_minus_data, ts, max_stdp_spike_delta)]
