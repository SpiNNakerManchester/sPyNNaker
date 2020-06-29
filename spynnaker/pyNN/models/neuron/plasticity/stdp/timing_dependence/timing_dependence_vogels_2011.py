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

import logging
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from spynnaker.pyNN.models.neuron.plasticity.stdp.timing_dependence import (
    AbstractTimingDependence)
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure import (
    SynapseStructureWeightOnly)
from spynnaker.pyNN.models.neuron.plasticity.stdp.common import (
    plasticity_helpers)
from spinn_front_end_common.utilities.globals_variables import get_simulator
from spynnaker.pyNN.models.neuron.plasticity.stdp.common\
    .plasticity_helpers import get_exp_lut_array

logger = logging.getLogger(__name__)


class TimingDependenceVogels2011(AbstractTimingDependence):
    __slots__ = [
        "__alpha",
        "__synapse_structure",
        "__tau",
        "__tau_data"]

    default_parameters = {'tau': 20.0}

    def __init__(self, alpha, tau=default_parameters['tau']):
        self.__alpha = alpha
        self.__tau = tau

        self.__synapse_structure = SynapseStructureWeightOnly()

        ts = get_simulator().machine_time_step / 1000.0
        self.__tau_data = get_exp_lut_array(ts, self.__tau)

    @property
    def alpha(self):
        return self.__alpha

    @property
    def tau(self):
        return self.__tau

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        # pylint: disable=protected-access
        if timing_dependence is None or not isinstance(
                timing_dependence, TimingDependenceVogels2011):
            return False
        return (self.__tau == timing_dependence.tau and
                self.__alpha == timing_dependence.alpha)

    @property
    def vertex_executable_suffix(self):
        return "vogels_2011"

    @property
    def pre_trace_n_bytes(self):
        # Trace entries consist of a single 16-bit number
        return BYTES_PER_SHORT

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return BYTES_PER_WORD + BYTES_PER_WORD * len(self.__tau_data)

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Write alpha to spec
        fixed_point_alpha = plasticity_helpers.float_to_fixed(self.__alpha)
        spec.write_value(data=fixed_point_alpha, data_type=DataType.INT32)

        # Write lookup table
        spec.write_array(self.__tau_data)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['alpha', 'tau']
