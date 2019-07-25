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
            routing_info):
        """ Write structural plasticity parameters
        """

    @abstractmethod
    def set_connections(
            self, connections, post_vertex_slice, app_edge, machine_edge):
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
