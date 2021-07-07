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
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.synapse_types import (
    SynapseTypeExpIzhikevichNeuromodulated)
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


class IFCondExpIzhikevichNeuromodulation(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an exponentially decaying \
        conductance input and neuromodulated synapses

    :param float tau_m: :math:`\\tau_m`
    :param float cm: :math:`C_m`
    :param float v_rest: :math:`V_{rest}`
    :param float v_reset: :math:`V_{reset}`
    :param float v_thresh: :math:`V_{thresh}`
    :param float tau_syn_E: :math:`\\tau^{syn}_e`
    :param float tau_syn_I: :math:`\\tau^{syn}_i`
    :param float tau_refrac: :math:`\\tau_{refrac}`
    :param float i_offset: :math:`I_{offset}`
    :param float e_rev_E: :math:`E^{rev}_e`
    :param float e_rev_I: :math:`E^{rev}_i`
    :param float v: :math:`V_{init}`
    :param float isyn_exc: :math:`I^{syn}_e`
    :param float isyn_inh: :math:`I^{syn}_i`
    """

    @default_initial_values({"v", "isyn_exc", "isyn_inh"})
    def __init__(
            self, tau_m=20.0, cm=1.0, v_rest=-65.0, v_reset=-65.0,
            v_thresh=-50.0, tau_syn_E=5.0, tau_syn_I=5.0, tau_refrac=0.1,
            i_offset=0.0, e_rev_E=0.0, e_rev_I=-70.0, v=-65.0,
            isyn_exc=0.0, isyn_inh=0.0):
        # pylint: disable=too-many-arguments, too-many-locals
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)
        synapse_type = SynapseTypeExpIzhikevichNeuromodulated(
            tau_syn_E, tau_syn_I, isyn_exc, isyn_inh)
        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCondExpIzhikevichNeuromodulation, self).__init__(
            model_name="IF_cond_expizkneuromod",
            binary="IF_cond_expizkneuromod.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
