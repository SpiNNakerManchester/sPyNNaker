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
    get_exp_lut_array)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)


class TimingDependencePfisterSpikeTriplet(AbstractTimingDependence):
    """ A timing dependence STDP rule based on spike triplets.

    Jean-Pascal Pfister, Wulfram Gerstner. Triplets of Spikes in a Model of
    Spike Timing-Dependent Plasticity. *Journal of Neuroscience*,
    20 September 2006, 26 (38) 9673-9682; DOI: 10.1523/JNEUROSCI.1425-06.2006
    """
    __slots__ = [
        "__synapse_structure",
        "__tau_minus",
        "__tau_minus_data",
        "__tau_plus",
        "__tau_plus_data",
        "__tau_x",
        "__tau_x_data",
        "__tau_y",
        "__tau_y_data",
        "__a_plus",
        "__a_minus"]
    __PARAM_NAMES = ('tau_plus', 'tau_minus', 'tau_x', 'tau_y')

    # noinspection PyPep8Naming
    def __init__(self, tau_plus, tau_minus, tau_x, tau_y, A_plus, A_minus):
        r"""
        :param float tau_plus: :math:`\tau_+`
        :param float tau_minus: :math:`\tau_-`
        :param float tau_x: :math:`\tau_x`
        :param float tau_y: :math:`\tau_y`
        :param float A_plus: :math:`A^+`
        :param float A_minus: :math:`A^-`
        """
        self.__tau_plus = tau_plus
        self.__tau_minus = tau_minus
        self.__tau_x = tau_x
        self.__tau_y = tau_y
        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self.__synapse_structure = SynapseStructureWeightOnly()

        ts = machine_time_step_ms()
        self.__tau_plus_data = get_exp_lut_array(ts, self.__tau_plus)
        self.__tau_minus_data = get_exp_lut_array(ts, self.__tau_minus)
        self.__tau_x_data = get_exp_lut_array(ts, self.__tau_x, shift=2)
        self.__tau_y_data = get_exp_lut_array(ts, self.__tau_y, shift=2)

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
    def tau_x(self):
        r""" :math:`\tau_x`

        :rtype: float
        """
        return self.__tau_x

    @property
    def tau_y(self):
        r""" :math:`\tau_y`

        :rtype: float
        """
        return self.__tau_y

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
        if not isinstance(
                timing_dependence, TimingDependencePfisterSpikeTriplet):
            return False
        return (
            (self.__tau_plus == timing_dependence.tau_plus) and
            (self.__tau_minus == timing_dependence.tau_minus) and
            (self.__tau_x == timing_dependence.tau_x) and
            (self.__tau_y == timing_dependence.tau_y))

    @property
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule

        :rtype: str
        """
        return "pfister_triplet"

    @property
    def pre_trace_n_bytes(self):
        """ The number of bytes used by the pre-trace of the rule per neuron

        :rtype: int
        """
        # Triplet rule trace entries consists of two 16-bit traces - R1 and R2
        # and the time of the last spike
        return BYTES_PER_WORD * 2

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        lut_array_words = (
            len(self.__tau_plus_data) + len(self.__tau_minus_data) +
            len(self.__tau_x_data) + len(self.__tau_y_data))
        return lut_array_words * BYTES_PER_WORD

    @property
    def n_weight_terms(self):
        """ The number of weight terms expected by this timing rule

        :rtype: int
        """
        return 2

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, weight_scales):

        # Write lookup tables
        spec.write_array(self.__tau_plus_data)
        spec.write_array(self.__tau_minus_data)
        spec.write_array(self.__tau_x_data)
        spec.write_array(self.__tau_y_data)

    @property
    def synaptic_structure(self):
        """ Get the synaptic structure of the plastic part of the rows

        :rtype: AbstractSynapseStructure
        """
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return self.__PARAM_NAMES
