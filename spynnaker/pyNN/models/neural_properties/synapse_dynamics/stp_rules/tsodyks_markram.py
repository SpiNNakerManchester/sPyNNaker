from data_specification.enums.data_type import DataType
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    plasticity_helpers import (float_to_fixed, write_exp_lut)
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    plastic_weight_synapse_row_io import PlasticWeightSynapseRowIo

import logging
import numpy
logger = logging.getLogger(__name__)

# Constants
# **NOTE** these should be passed through magical per-vertex build setting
# thing
TAU_SYN_LUT_SHIFT = 0
TAU_SYN_LUT_SIZE = 256
TAU_REC_LUT_SHIFT = 3
TAU_REC_LUT_SIZE = 1136
TAU_FAC_LUT_SHIFT = 3
TAU_FAC_LUT_SIZE = 1136

class TsodyksMarkramMechanism(object):
    """
    Synapse exhibiting facilitation and depression, implemented using the model
    of Tsodyks, Markram et al.:

    Tsodyks, Uziel, Markram (2000) Synchrony Generation in Recurrent Networks
    with Frequency-Dependent Synapses. Journal of Neuroscience, vol 20 RC50

    Note that the time constant of the post-synaptic current is set in the
    neuron model, not here.
    """
    vertex_executable_suffix = "stp_tsodyks_markram"

    def __init__(self, U=0.5, tau_rec=100.0, tau_facil=0.0, u0=0.0, x0=1.0, y0=0.0):
        self._U = U
        self._tau_rec = tau_rec
        self._tau_fac = tau_facil
        self._u0 = u0
        self._x0 = x0
        self._y0 = y0

    @property
    def synaptic_row_header_words(self):
        # Convert initial parameters to fixed-point
        u0_fixed = float_to_fixed(self._u0)
        x0_fixed = float_to_fixed(self._x0)
        y0_fixed = float_to_fixed(self._y0)

        # Create 4 element array of 16-bit values and return word
        return numpy.asarray([u0_fixed, x0_fixed, y0_fixed, 0],
                             dtype="int16").view(dtype="uint32")

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, TsodyksMarkramMechanism)):
            return False
        return ((self._U == other._U) and
                (self._tau_rec == other._tau_rec) and
                (self._tau_fac == other._tau_fac) and
                (self._u0 == other._u0) and
                (self._x0 == other._x0) and
                (self._y0 == other._y0))

    def create_synapse_row_io(self):
        return PlasticWeightSynapseRowIo(self.synaptic_row_header_words, 1.0)

    def write_plastic_params(self, spec, region, machine_time_step, vertex):
        """ method that writes plastic params to a data spec generator

        :param spec:
        :param machine_time_step:
        :return:
        """

        # Switch focus to the region:
        spec.switch_write_focus(region)

        # **YUCK** get time constant of PSC from vertex
        # this needs more thought as I suspect this will, incorrectly work with alpha synapses
        # also should be calculated seperately for all synapse types on vertex
        tau_psc = float(vertex.tau_syn_E)

        # Calculate multipliers for p_xy calculation
        tau_rec_over_psc_rec = float(self._tau_rec) / (tau_psc - float(self._tau_rec))
        tau_psc_over_psc_rec = float(self._tau_rec) / (tau_psc - float(self._tau_rec))

        # Check timestep is valid
        if machine_time_step != 1000:
            raise NotImplementedError("STP LUT generation currently only "
                                      "supports 1ms timesteps")

        # Write constants
        spec.write_value(data=float_to_fixed(self._U),
                         data_type=DataType.INT32)
        spec.write_value(data=float_to_fixed(tau_rec_over_psc_rec),
                         data_type=DataType.INT32)
        spec.write_value(data=float_to_fixed(tau_psc_over_psc_rec),
                         data_type=DataType.INT32)

        # Write lookup tables
        write_exp_lut(spec, tau_psc, TAU_SYN_LUT_SIZE, TAU_SYN_LUT_SHIFT)
        write_exp_lut(spec, self._tau_rec, TAU_REC_LUT_SIZE, TAU_REC_LUT_SHIFT)
        write_exp_lut(spec, self._tau_fac, TAU_FAC_LUT_SIZE, TAU_FAC_LUT_SHIFT)

    def get_params_size_bytes(self):
        # Calculate combined size of all three LUTs
        lut_size_bytes = 2 * (TAU_SYN_LUT_SIZE + TAU_REC_LUT_SIZE + TAU_FAC_LUT_SIZE)

        # Add size of 3 constants
        return lut_size_bytes + (3 * 4)