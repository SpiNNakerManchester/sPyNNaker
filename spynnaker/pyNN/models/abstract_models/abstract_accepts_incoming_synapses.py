from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty
from spinn_utilities.abstract_base import abstractmethod


@add_metaclass(AbstractBase)
class AbstractAcceptsIncomingSynapses(object):
    """ Indicates an object that can be a post-vertex in a PyNN projection
    """

    @abstractproperty
    def synapse_type(self):
        """ The synapse type of the vertex

        :rtype:\
            :py:class:`spynnaker.pyNN.models.neuron.synapse_types.abstract_synapse_type.AbstractSynapseType`
        """
        pass

    @abstractmethod
    def set_synapse_dynamics(self, synapse_dynamics):
        """ Set the synapse dynamics of this vertex
        """
        pass

    @abstractmethod
    def get_maximum_delay_supported_in_ms(self, machine_time_step):
        """ Get the maximum delay supported by this vertex
        """
        pass

    @abstractmethod
    def add_pre_run_connection_holder(
            self, connection_holder, projection_edge, synapse_information):
        """ Add a connection holder to the vertex to be filled in when the\
            connections are actually generated
        """
        pass

    @abstractmethod
    def get_connections_from_machine(
            self, transceiver, placement, edge, graph_mapper, routing_infos,
            synapse_information, machine_time_step):
        """ Get the connections from the machine post-run
        """
        pass
