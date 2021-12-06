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
from spynnaker.pyNN.models.defaults import defaults, default_initial_values
from spynnaker.pyNN.models.neuron.neuron_models import (
    NeuronModelLeakyIntegrateAndFire)
from spynnaker.pyNN.models.neuron.synapse_types import SynapseTypeAlpha
from spynnaker.pyNN.models.neuron.input_types import InputTypeConductance
from spynnaker.pyNN.models.neuron.threshold_types import ThresholdTypeStatic


@defaults
class IFCondAlpha(AbstractPyNNNeuronModelStandard):
    """ Leaky integrate and fire neuron with an alpha-shaped current input.

    .. warning::

        Not currently supported by the tool chain.
    """

    # noinspection PyPep8Naming
    @default_initial_values({"v", "exc_response",
                             "exc_exp_response", "inh_response",
                             "inh_exp_response"})
    def __init__(
            self, tau_m=20, cm=1.0, e_rev_E=0.0, e_rev_I=-70.0, v_rest=-65.0,
            v_reset=-65.0, v_thresh=-50.0, tau_syn_E=0.3, tau_syn_I=0.5,
            tau_refrac=0.1, i_offset=0, v=-65.0,
            exc_response=0.0, exc_exp_response=0.0, inh_response=0.0,
            inh_exp_response=0.0):
        # pylint: disable=too-many-arguments, too-many-locals, unused-argument
        neuron_model = NeuronModelLeakyIntegrateAndFire(
            v, v_rest, tau_m, cm, i_offset, v_reset, tau_refrac)

        synapse_type = SynapseTypeAlpha(
            exc_response=exc_response, exc_exp_response=exc_exp_response,
            tau_syn_E=tau_syn_E, inh_response=inh_response,
            inh_exp_response=inh_exp_response, tau_syn_I=tau_syn_I)

        input_type = InputTypeConductance(e_rev_E, e_rev_I)
        threshold_type = ThresholdTypeStatic(v_thresh)

        super(IFCondAlpha, self).__init__(
            model_name="IF_cond_alpha", binary="IF_cond_alpha.aplx",
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type)
