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
from spynnaker.pyNN.models.neuron.implementations import MeanfieldImplStandard
from spinn_utilities.overrides import overrides

_population_parameters = dict(
    AbstractPyNNNeuronModel.default_population_parameters)
_population_parameters["n_steps_per_timestep"] = 1


class AbstractPyNNMeanfieldModelStandard(AbstractPyNNNeuronModel):
    """ A neuron model that follows the sPyNNaker standard composed model \
        pattern for point neurons.
    """

    __slots__ = []

    default_population_parameters = _population_parameters

    def __init__(
            self, model_name, binary, neuron_model, config,
        mathsbox, input_type, synapse_type, threshold_type,
        additional_input_type=None):
        """
        :param str model_name: Name of the model.
        :param str binary: Name of the implementation executable.
        :param AbstractNeuronModel neuron_model: The model of the neuron soma
        :param AbstractInputType input_type: The model of synaptic input types
        :param AbstractSynapseType synapse_type:
            The model of the synapses' dynamics
        :param AbstractThresholdType threshold_type:
            The model of the firing threshold
        :param additional_input_type:
            The model (if any) of additional environmental inputs
        :type additional_input_type: AbstractAdditionalInput or None
        """
        super().__init__(MeanfieldImplStandard(
            model_name, binary, neuron_model, config, mathsbox, input_type,
            synapse_type, threshold_type, additional_input_type))

    @overrides(AbstractPyNNNeuronModel.create_vertex,
               additional_arguments={"n_steps_per_timestep"})
    def create_vertex(
            self, n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size,
            n_steps_per_timestep, drop_late_spikes, splitter):
        # pylint: disable=arguments-differ
        self._model.n_steps_per_timestep = n_steps_per_timestep
        return super().create_vertex(
            n_neurons, label, constraints, spikes_per_second,
            ring_buffer_sigma, incoming_spike_buffer_size, drop_late_spikes,
            splitter)
