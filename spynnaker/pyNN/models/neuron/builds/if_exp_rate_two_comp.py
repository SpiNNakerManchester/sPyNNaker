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
    NeuronModelLeakyIntegrateAndFireTwoCompRate)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeExponentialTwoComp
from spynnaker.pyNN.models.neuron.input_types import InputTypeTwoComp
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class IFExpRateTwoComp(AbstractPyNNNeuronModelStandard):
    """ Multicompartment model from Urbanczik and Senn
    """

    __slots__ = ["_rate_based"]

    @default_initial_values({"u", "isyn_exc_soma", "isyn_inh_soma",
                             "isyn_exc_dendrite", "isyn_inh_dendrite",
                             "v", "starting_rate"})
    def __init__(
            self, cm=1.0, u_rest=0, v_reset=-50.0,
            v_thresh=10.0, i_offset=0.0, u=0.0,

            g_som=0.8,

            tau_syn_E_soma=5.0, tau_syn_I_soma=5.0,
            isyn_exc_soma =0.0, isyn_inh_soma=0.0,

            tau_syn_E_dendrite=5.0, tau_syn_I_dendrite=5.0,
            isyn_exc_dendrite=0.0, isyn_inh_dendrite=0.0,

            g_D=2, g_L=0.1, tau_L=10, v=0.0,

            rate_update_threshold=2,

            starting_rate=0, teach=True, out=False
            ):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFireTwoCompRate(
            u, u_rest, cm, i_offset, v_reset, g_D, g_L, g_som,
            tau_L, v, rate_update_threshold, starting_rate)
        synapse_type = SynapseTypeExponentialTwoComp(
            tau_syn_E_soma, tau_syn_E_dendrite, tau_syn_I_soma, tau_syn_I_dendrite,
            isyn_exc_soma, isyn_exc_dendrite, isyn_inh_soma, isyn_inh_dendrite)
        input_type = InputTypeTwoComp()
        threshold_type = ThresholdTypeStatic(v_thresh)

        self._rate_based = True

        if out:
            super(IFExpRateTwoComp, self).__init__(
                model_name="IF_exp_rate_two_comp", binary="Two_comp_rate_out.aplx",
                neuron_model=neuron_model, input_type=input_type,
                synapse_type=synapse_type, threshold_type=threshold_type)
        elif teach:
            super(IFExpRateTwoComp, self).__init__(
                model_name="IF_exp_rate_two_comp", binary="Two_comp_rate.aplx",
                neuron_model=neuron_model, input_type=input_type,
                synapse_type=synapse_type, threshold_type=threshold_type)
        else:
            super(IFExpRateTwoComp, self).__init__(
                model_name="IF_exp_rate_two_comp", binary="Two_comp_rate_no_teach.aplx",
                neuron_model=neuron_model, input_type=input_type,
                synapse_type=synapse_type, threshold_type=threshold_type)
