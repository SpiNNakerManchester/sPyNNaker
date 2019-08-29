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
    NeuronModelLeakyIntegrateAndFireTwoComp)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponentialTwoComp
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class IFCurrExpTwoComp(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        current input to soma and dendrite
    """

    @default_initial_values({"u", "isyn_exc_soma", "isyn_inh_soma",
                             "isyn_exc_dendrite", "isyn_inh_dendrite",
                             "v", "v_star",
                             "mean_isi_ticks", "time_to_spike_ticks"})
    def __init__(
            self, tau_m=0.5, cm=1.0, u_rest=0, v_reset=0.0,
            v_thresh=10.0, tau_refrac=0.1, i_offset=0.0, u=0.0,

            tau_syn_E_soma=5.0, tau_syn_I_soma=5.0,
            isyn_exc_soma =0.0, isyn_inh_soma=0.0,

            tau_syn_E_dendrite=5.0, tau_syn_I_dendrite=5.0,
            isyn_exc_dendrite=0.0, isyn_inh_dendrite=0.0,

            g_D=2, g_L=0.1, tau_L=10, v=0.0, v_star=0.0,

            mean_isi_ticks=65000, time_to_spike_ticks=65000, rate_update_threshold=0.25
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireTwoComp(
            u, u_rest, tau_m, cm, i_offset, v_reset, tau_refrac,
            g_D, g_L, tau_L, v, v_star,
            mean_isi_ticks, time_to_spike_ticks, rate_update_threshold)
        synapse_type = SynapseTypeExponentialTwoComp(
            tau_syn_E_soma, tau_syn_E_dendrite, tau_syn_I_soma, tau_syn_I_dendrite,
            isyn_exc_soma, isyn_exc_dendrite, isyn_inh_soma, isyn_inh_dendrite)
        input_type = InputTypeCurrent()
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCurrExpTwoComp, self).__init__(
            model_name="IF_curr_exp_two_comp", binary="IF_curr_exp_two_comp.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
