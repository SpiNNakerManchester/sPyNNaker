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

from spynnaker.pyNN.models.neuron import AbstractPyNNNeuronModelStandard
from spynnaker.pyNN.models.defaults import default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelPyramidalRate)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypePyramidal
from spynnaker.pyNN.models.neuron.input_types import InputTypePyramidal
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class PyramidalRate(AbstractPyNNNeuronModelStandard):
    """ Pyramidal model
    """

    __slots__ = ["_rate_based"]

    @default_initial_values({"u", "isyn_exc_apical", "isyn_inh_apical",
                             "isyn_exc_basal", "isyn_inh_basal",
                             "v_A", "v_B", "starting_rate"})
    def __init__(
            self, cm=1.0, u_rest=0, v_reset=-50.0,
            v_thresh=10.0, i_offset=0.0, u=0.0,

            tau_syn_E_apical=5.0, tau_syn_I_apical=5.0,
            isyn_exc_apical =0.0, isyn_inh_apical=0.0,

            tau_syn_E_basal=5.0, tau_syn_I_basal=5.0,
            isyn_exc_basal=0.0, isyn_inh_basal=0.0,

            g_A=0.8, g_L=0.1, tau_L=10, g_B=1.0,
            v_A=0.0, v_B=0.0,

            rate_update_threshold=2,

            starting_rate=0,
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelPyramidalRate(
            u, u_rest, cm, i_offset, v_reset, v_A, v_B, g_A, g_B, g_L,
            tau_L, v_A, rate_update_threshold, starting_rate)
        synapse_type = SynapseTypePyramidal(
            tau_syn_E_apical, tau_syn_E_basal, tau_syn_I_apical, tau_syn_I_basal,
            isyn_exc_apical, isyn_exc_basal, isyn_inh_apical, isyn_inh_basal)
        input_type = InputTypePyramidal()
        threshold_type = ThresholdTypeStatic(v_thresh)

        self._rate_based = True

        super(PyramidalRate, self).__init__(
            model_name="Pyramidal_rate", binary="Pyramidal_rate.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
