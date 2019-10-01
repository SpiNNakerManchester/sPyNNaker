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

from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractproperty, abstractmethod)


@add_metaclass(AbstractBase)
class AbstractSynapseDynamicsStructural(object):

    @abstractmethod
    def get_structural_parameters_sdram_usage_in_bytes(
            self, application_graph, app_vertex, n_neurons, n_synapse_types):
        """ Get the size of the structural parameters
        """

    @abstractmethod
    def write_structural_parameters(
            self, spec, region, machine_time_step, weight_scales,
            application_graph, app_vertex, post_slice, graph_mapper,
            routing_info, synapse_indices):
        """ Write structural plasticity parameters
        """

    @abstractmethod
    def set_connections(
            self, connections, post_vertex_slice, app_edge, synapse_info,
            machine_edge):
        """ Set connections for structural plasticity
        """

    @abstractproperty
    def f_rew(self):
        """ The frequency of rewiring
        """

    @abstractproperty
    def s_max(self):
        """ The maximum number of synapses
        """

    @abstractproperty
    def seed(self):
        """ The seed to control the randomness
        """

    @abstractproperty
    def initial_weight(self):
        """ The weight of a formed connection
        """

    @abstractproperty
    def initial_delay(self):
        """ The delay of a formed connection
        """

    @abstractproperty
    def partner_selection(self):
        """ The partner selection rule
        """

    @abstractproperty
    def formation(self):
        """ The formation rule
        """

    @abstractproperty
    def elimination(self):
        """ The elimination rule
        """
