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

from .abstract_pynn_neuron_model import AbstractPyNNNeuronModel
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStandard


class AbstractPyNNNeuronModelStandard(AbstractPyNNNeuronModel):
    """ A neuron model that follows the sPyNNaker standard composed model \
        pattern for point neurons.
    """

    __slots__ = []

    def __init__(
            self, model_name, binary, neuron_model, input_type,
            synapse_type, threshold_type, additional_input_type=None):
        """
        :param model_name: Name of the model.
        :type model_name: str
        :param binary: Name of the implementation executable.
        :type binary: str
        :param neuron_model: The model of the neuron soma
        :type neuron_model: AbstractNeuronModel
        :param input_type: The model of synaptic input types
        :type input_type: AbstractInputType
        :param synapse_type: The model of the synapses' dynamics
        :type synapse_type: AbstractSynapseType
        :param threshold_type: The model of the firing threshold
        :type threshold_type: AbstractThresholdType
        :param additional_input_type: \
            The model (if any) of additional environmental inputs
        :type additional_input_type: AbstractAdditionalInput or None
        """
        AbstractPyNNNeuronModel.__init__(self, NeuronImplStandard(
            model_name, binary, neuron_model, input_type, synapse_type,
            threshold_type, additional_input_type))
