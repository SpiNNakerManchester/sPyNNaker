# Copyright (c) 2017-2019 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spynnaker.pyNN.data import SpynnakerDataView
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.models.neuron.plasticity.stdp.common \
    import write_mfvn_lut
from .abstract_timing_dependence import AbstractTimingDependence
from spynnaker.pyNN.models.neuron.plasticity.stdp.synapse_structure\
    import SynapseStructureWeightOnly


import logging
logger = logging.getLogger(__name__)

LUT_SIZE = 256


class TimingDependenceMFVN(AbstractTimingDependence):
    __slots__ = [
        "_synapse_structure",
        "_tau_minus",
        "_tau_minus_data",
        "_tau_plus",
        "_tau_plus_data",
        "__a_plus",
        "__a_minus",
        "_beta",
        "_sigma",
        "_alpha"
        ]

    def __init__(self, tau_plus=20.0, tau_minus=20.0, A_plus=0.01,
                 A_minus=0.01, beta=10, sigma=200, alpha=1.0):
        self._tau_plus = tau_plus
        self._tau_minus = tau_minus

        self.__a_plus = A_plus
        self.__a_minus = A_minus

        self._alpha = alpha

        self._synapse_structure = SynapseStructureWeightOnly()

        self._beta = beta
        self._sigma = sigma

        # provenance data
        self._tau_plus_data = None
        self._tau_minus_data = None

    @property
    def tau_plus(self):
        return self._tau_plus

    @property
    def tau_minus(self):
        return self._tau_minus

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

    @property
    def beta(self):
        return self._beta

    @property
    def sigma(self):
        return self._sigma

    @overrides(AbstractTimingDependence.is_same_as)
    def is_same_as(self, timing_dependence):
        if not isinstance(timing_dependence, TimingDependenceMFVN):
            return False
        return (self.tau_plus == timing_dependence.tau_plus and
                self.tau_minus == timing_dependence.tau_minus)

    @property
    def vertex_executable_suffix(self):
        return "mfvn"

    @property
    def pre_trace_n_bytes(self):
        # Here we will record the last 16 spikes,
        # these will be 32-bit quantities,
        # 16 4-byte entries, plus one counter for the number of spikes
        return (16 * 4) + (2 * 16)

    @overrides(AbstractTimingDependence.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return BYTES_PER_WORD * LUT_SIZE

    @property
    def n_weight_terms(self):
        return 1

    @overrides(AbstractTimingDependence.write_parameters)
    def write_parameters(
            self, spec, global_weight_scale, synapse_weight_scales):
        # Check timestep is valid
        time_step = SpynnakerDataView.get_simulation_time_step_ms()
        if time_step != 1:
            raise NotImplementedError(
                "exp cos LUT generation currently only supports 1ms timesteps")

        # Write exp_sin lookup table
        self._tau_plus_data = write_mfvn_lut(
            spec,
            sigma=self._sigma,
            beta=self._beta,
            time_probe=None,
            lut_size=LUT_SIZE,
            shift=0,
            kernel_scaling=self._alpha)

    @property
    def synaptic_structure(self):
        return self._synapse_structure

    @overrides(AbstractTimingDependence.get_provenance_data)
    def get_provenance_data(self, synapse_info):
        tauplus = 0
        if self._tau_plus_data is not None:
            tauplus = self._tau_plus_data[-1]
        tauminus = 0
        if self._tau_minus_data is not None:
            tauminus = self._tau_minus_data[-1]
        with ProvenanceWriter() as db:
            db.insert_lut(
                synapse_info.pre_population.label,
                synapse_info.post_population.label,
                self.__class__.__name__, "tau_plus last_entry",
                tauplus)
            if tauplus > 0:
                db.insert_report(
                    f"The last entry in the STDP exponential lookup table "
                    f"for the tau_plus parameter of the"
                    f"{self.__class__.__name__} between "
                    f"{synapse_info.pre_population.label} and "
                    f"{synapse_info.post_population.label} was {tauplus} "
                    f"rather than 0, indicating that the lookup table was "
                    f"not big enough at this timestep and value.  Try "
                    f"reducing the parameter value, or increasing the "
                    f"timestep.")
            db.insert_lut(
                synapse_info.pre_population.label,
                synapse_info.post_population.label,
                self.__class__.__name__, "tau_minus last_entry",
                tauminus)
            if tauminus > 0:
                db.insert_report(
                    f"The last entry in the STDP exponential lookup table "
                    f"for the tau_minus parameter of the "
                    f"{self.__class__.__name__} between "
                    f"{synapse_info.pre_population.label} and "
                    f"{synapse_info.post_population.label} was {tauminus} "
                    f"rather than 0, indicating that the lookup table was "
                    f"not big enough at this timestep and value.  Try "
                    f"reducing the parameter value, or increasing the "
                    f"timestep.")

    @overrides(AbstractTimingDependence.get_parameter_names)
    def get_parameter_names(self):
        return ['tau_plus', 'tau_minus', 'beta', 'sigma']