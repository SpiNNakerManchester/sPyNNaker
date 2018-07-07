from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase
from spinn_utilities.abstract_base import abstractproperty, abstractmethod


@add_metaclass(AbstractBase)
class AbstractAcceptsIncomingSynapses(object):
    """ Indicates an object that can be a post-vertex in a PyNN projection
    """
    __slots__ = ()

    @abstractproperty
    def get_synapse_id_by_target(self, target):
        """ Get the id of a synapse given the name

        :param target: The name of the synapse
        :type target: str
        :rtype: int
        """

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
            synapse_information, machine_time_step,
            using_extra_monitor_cores, placements=None, data_receiver=None,
            sender_extra_monitor_core_placement=None,
            extra_monitor_cores_for_router_timeout=None,
            handle_time_out_configuration=True, fixed_routes=None):
        # pylint: disable=too-many-arguments
        """ Get the connections from the machine post-run
        """
        pass

    @abstractmethod
    def clear_connection_cache(self):
        """ clears the connection data stored in the vertex so far.
        """
