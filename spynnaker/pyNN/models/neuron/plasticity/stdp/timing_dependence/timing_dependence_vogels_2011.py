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
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.data import SpynnakerDataView
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    float_to_fixed, get_exp_lut_array, get_min_lut_value)


class TimingDependenceVogels2011(AbstractTimingDependence):
    """ A timing dependence STDP rule due to Vogels (2011).
    """
    __slots__ = [
        "__alpha",
        "__synapse_structure",
        "__tau",
        "__tau_data",
        "__a_plus",
        "__a_minus"]
    __PARAM_NAMES = ('alpha', 'tau')
    default_parameters = {'tau': 20.0}

    def __init__(self, alpha, tau=default_parameters['tau'],
                 A_plus=0.01, A_minus=0.01):
        r"""
        :param float alpha: :math:`\alpha`
        :param float tau: :math:`\tau`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        self.__alpha = alpha
        self.__tau = tau
        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self.__synapse_structure = SynapseStructureWeightOnly()

        self.__tau_data = get_exp_lut_array(
            SpynnakerDataView.get_simulation_time_step_ms(), self.__tau)

    @property
    def alpha(self):
        r""" :math:`\alpha`

        :rtype: float
        """
        return self.__alpha

    @property
    def tau(self):
        r""" :math:`\tau`

        :rtype: float
        """
        return self.__tau

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
        if not isinstance(timing_dependence, TimingDependenceVogels2011):
            return False
        return (self.__tau == timing_dependence.tau and
                self.__alpha == timing_dependence.alpha)

    @property
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """
        return "vogels_2011"

    @property
    def pre_trace_n_bytes(self):
        """ The number of bytes used by the pre-trace of the rule per neuron

        :rtype: int
        """
        # Trace entries consist of a single 16-bit number
        return BYTES_PER_SHORT

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return BYTES_PER_WORD + BYTES_PER_WORD * len(self.__tau_data)

    @property
    def n_weight_terms(self):
        """ The number of weight terms expected by this timing rule

        :rtype: int
        """
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales):

        # Write alpha to spec
        fixed_point_alpha = float_to_fixed(self.__alpha)
        spec.write_value(data=fixed_point_alpha, data_type=DataType.INT32)

        # Write lookup table
        spec.write_array(self.__tau_data)

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
        ts = SpynnakerDataView.get_simulation_time_step_ms()
        min_tau = get_min_lut_value(self.__tau_data, ts, max_stdp_spike_delta)
        return [min_tau - self.__alpha, min_tau]
