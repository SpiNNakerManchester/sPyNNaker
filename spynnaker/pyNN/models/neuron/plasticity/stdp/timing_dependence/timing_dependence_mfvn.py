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
from spinn_front_end_common.interface.provenance import ProvenanceWriter
from spinn_front_end_common.utilities.globals_variables import (
    machine_time_step_ms)
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
        "_tau_minus_last_entry",
        "_tau_plus",
        "_tau_plus_last_entry",
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
        self._tau_plus_last_entry = None
        self._tau_minus_last_entry = None

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
        machine_time_step = machine_time_step_ms()
        if machine_time_step != 1:
            raise NotImplementedError(
                "exp cos LUT generation currently only supports 1ms timesteps")

        # Write exp_sin lookup table
        self._tau_plus_last_entry = write_mfvn_lut(
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
        tauplus = self._tau_plus_last_entry
        tauminus = self._tau_minus_last_entry
        with ProvenanceWriter() as db:
            db.insert_lut(
                synapse_info.pre_population.label,
                synapse_info.post_population.label,
                self.__class__.__name__, "tau_plus_last_entry",
                tauplus)
            if tauplus is not None:
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
                self.__class__.__name__, "tau_minus_last_entry",
                tauminus)
            if tauminus is not None:
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
