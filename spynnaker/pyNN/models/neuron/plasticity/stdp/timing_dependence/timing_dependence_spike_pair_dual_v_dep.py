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


class TimingDependenceSpikePairDualVDep(AbstractTimingDependence):
    __slots__ = [
        "__alpha_exc",
        "__alpha_inh",
        "__synapse_structure",
        "__tau_exc",
        "__tau_exc_data",
        "__tau_inh",
        "__tau_inh_data"]

    #default_parameters = {'tau': 20.0, 'tau_plus': 20.0, 'tau_minus': 20.0}

    def __init__(self, alpha_exc, alpha_inh, tau_exc=20.0, tau_inh=20.0):
        self.__alpha_exc = alpha_exc
        self.__alpha_inh = alpha_inh
        self.__tau_exc = tau_exc
        self.__tau_inh = tau_inh

        self.__synapse_structure = SynapseStructureWeightOnly()

        ts = get_simulator().machine_time_step / 1000.0
        self.__tau_exc_data = get_exp_lut_array(ts, self.__tau_exc)
        self.__tau_inh_data = get_exp_lut_array(ts, self.__tau_inh)

    @property
    def alpha_exc(self):
        return self.__alpha_exc

    @property
    def alpha_inh(self):
        return self.__alpha_inh

    @property
    def tau_exc(self):
        return self.__tau_exc

    @property
    def tau_inh(self):
        return self.__tau_inh

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        # pylint: disable=protected-access
        if timing_dependence is None or not isinstance(
                timing_dependence, TimingDependenceSpikePairDualVDep):
            return False
        return (self.__tau_exc == timing_dependence.tau_exc and
                self.__alpha_exc == timing_dependence.alpha_exc and
                self.__tau_inh == timing_dependence.tau_plus and
                self.__alpha_inh == timing_dependence.alpha_inh)


    @property
    def vertex_executable_suffix(self):
        return "dual_v_dep_pair_dual_v_dep"

    @property
    def pre_trace_n_bytes(self):
        # Trace entries consist of a single 16-bit number
        return BYTES_PER_SHORT

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return (2 * BYTES_PER_WORD + BYTES_PER_WORD * (len(self.__tau_exc_data)
                                                        + len(self.__tau_inh_data)))

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(self, spec, machine_time_step, weight_scales):

        # Write alpha to spec
        fixed_point_alpha_exc = plasticity_helpers.float_to_fixed(
            self.__alpha_exc, plasticity_helpers.STDP_FIXED_POINT_ONE)
        spec.write_value(data=fixed_point_alpha_exc, data_type=DataType.INT32)

        fixed_point_alpha_inh = plasticity_helpers.float_to_fixed(
            self.__alpha_inh, plasticity_helpers.STDP_FIXED_POINT_ONE)
        spec.write_value(data=fixed_point_alpha_inh, data_type=DataType.INT32)

        # Write lookup table
        spec.write_array(self.__tau_exc)
        spec.write_array(self.__tau_inh)

    @property
    def synaptic_structure(self):
        return self.__synapse_structure

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['alpha_exc', 'alpha_inh', 'tau_exc', 'tau_inh']
