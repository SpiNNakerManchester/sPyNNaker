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

from pyNN import descriptions
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.abstract_pynn_model import AbstractPyNNModel
from spynnaker.pyNN.utilities.constants import POP_TABLE_MAX_ROW_LENGTH

# The maximum atoms per core is the master population table row length to
# make it easier when all-to-all-connector is used
DEFAULT_MAX_ATOMS_PER_CORE = POP_TABLE_MAX_ROW_LENGTH

_population_parameters = {
    "spikes_per_second": None, "ring_buffer_sigma": None,
    "incoming_spike_buffer_size": None, "drop_late_spikes": None,
    "splitter": None, "seed": None, "n_colour_bits": None
}


class AbstractPyNNNeuronModel(AbstractPyNNModel):
    __slots__ = ["__model"]

    default_population_parameters = _population_parameters

    def __init__(self, model):
        """
        :param AbstractNeuronImpl model: The model implementation
        """
        self.__model = model

    @property
    def _model(self):
        return self.__model

    @overrides(AbstractPyNNModel.create_vertex,
               additional_arguments=_population_parameters.keys())
    def create_vertex(
            self, n_neurons, label, spikes_per_second, ring_buffer_sigma,
            incoming_spike_buffer_size, drop_late_spikes, splitter, seed,
            n_colour_bits):
        # pylint: disable=arguments-differ
        max_atoms = self.get_model_max_atoms_per_dimension_per_core()
        return AbstractPopulationVertex(
            n_neurons, label, max_atoms, spikes_per_second, ring_buffer_sigma,
            incoming_spike_buffer_size, self.__model, self, drop_late_spikes,
            splitter, seed, n_colour_bits)

    @property
    def name(self):
        return self.__model.model_name

    def describe(self, template='modeltype_default.txt', engine='default'):
        """ Returns a human-readable description of the population.

        The output may be customized by specifying a different template
        together with an associated template engine (see
        :mod:`pyNN.descriptions`).

        If ``template`` is ``None``, then a dictionary containing the template
        context will be returned.

        :param str template: Template filename
        :param engine: Template substitution engine
        :type engine: str or ~pyNN.descriptions.TemplateEngine or None
        :rtype: str or dict
        """
        context = {
            "name": self.name
        }
        return descriptions.render(engine, template, context)
