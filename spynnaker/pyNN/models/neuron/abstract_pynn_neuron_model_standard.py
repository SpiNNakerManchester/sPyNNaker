# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .abstract_pynn_neuron_model import AbstractPyNNNeuronModel
from spynnaker.pyNN.models.neuron.implementations import NeuronImplStandard
from spinn_utilities.overrides import overrides

_population_parameters = dict(
    AbstractPyNNNeuronModel.default_population_parameters)
_population_parameters["n_steps_per_timestep"] = 1


class AbstractPyNNNeuronModelStandard(AbstractPyNNNeuronModel):
    """
    A neuron model that follows the sPyNNaker standard composed model
    pattern for point neurons.
    """

    __slots__ = []

    default_population_parameters = _population_parameters

    def __init__(
            self, model_name, binary, neuron_model, input_type,
            synapse_type, threshold_type, additional_input_type=None):
        """
        :param str model_name: Name of the model.
        :param str binary: Name of the implementation executable.
        :param AbstractPyNNNeuronModel neuron_model:
            The model of the neuron soma
        :param AbstractInputType input_type: The model of synaptic input types
        :param AbstractSynapseType synapse_type:
            The model of the synapses' dynamics
        :param AbstractThresholdType threshold_type:
            The model of the firing threshold
        :param additional_input_type:
            The model (if any) of additional environmental inputs
        :type additional_input_type: AbstractAdditionalInput or None
        """
        super().__init__(NeuronImplStandard(
            model_name, binary, neuron_model, input_type, synapse_type,
            threshold_type, additional_input_type))

    @overrides(AbstractPyNNNeuronModel.create_vertex,
               additional_arguments={"n_steps_per_timestep"})
    def create_vertex(
            self, n_neurons, label, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size,
            n_steps_per_timestep, drop_late_spikes, splitter, seed,
            n_colour_bits, rb_left_shifts):
        """
        :param int n_steps_per_timestep:
        """
        # pylint: disable=arguments-differ
        self._model.n_steps_per_timestep = n_steps_per_timestep
        return super().create_vertex(
            n_neurons, label, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size, drop_late_spikes,
            splitter, seed, n_colour_bits, rb_left_shifts)
