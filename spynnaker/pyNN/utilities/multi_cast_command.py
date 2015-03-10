from spynnaker.pyNN.exceptions import SpynnakerException


class MultiCastCommand(object):
    """ A command to be sent to a vertex
    """

    def __init__(self, time, key, mask=0xFFFFFFFF, payload=None, repeat=0,
                 delay_between_repeats=0):
        """

        :param time: The time within the simulation at which to send the\
                    commmand.  0 or a positive value indicates the number of\
                    timesteps after the start of the simulation at which\
                    the command is to be sent.  A negative value indicates the\
                    (number of timesteps - 1) before the end of simulation at\
                    which the command is to be sent (thus -1 means the last\
                    timestep of the simulation).
        :type time: int
        :param key: The key of the command
        :type key: int
        :param mask: A mask to indicate the important bits of the command key.\
                    By default, all bits are assumed to be important, but this\
                    can be used to optimize the sending of a group of commands
        :type mask: int
        :param payload: The payload of the command
        :type payload: int
        :param repeat: The number of times that the command should be\
                    repeated after sending it once.  This could be used to\
                    ensure that the command is sent despite lost packets.\
                    Must be between 0 and 65535
        :type repeat: int
        :param delay_between_repeats: The amount of time in micro seconds to\
                    wait between sending repeats of the same command.\
                    Must be between 0 and 65535, and must be 0 if repeat is 0
        :type delay_between_repeats: int
        :raise SpynnakerException: If the repeat or delay are out of range
        """

        if repeat < 0 or repeat > 0xFFFF:
            raise SpynnakerException("repeat must be between 0 and 65535")
        if delay_between_repeats < 0 or delay_between_repeats > 0xFFFF:
            raise SpynnakerException(
                "delay_between_repeats must be between 0 and 65535")
        if delay_between_repeats > 0 and repeat == 0:
            raise SpynnakerException(
                "If repeat is 0, delay_betweeen_repeats must be 0")

        self._time = time
        self._key = key
        self._mask = mask
        self._payload = payload
        self._repeat = repeat
        self._delay_between_repeats = delay_between_repeats

    @property
    def time(self):
        return self._time

    @property
    def key(self):
        return self._key

    @property
    def mask(self):
        return self._mask

    @property
    def repeat(self):
        return self._repeat

    @property
    def delay_between_repeats(self):
        return self._delay_between_repeats

    def get_payload(self, routing_info, partitioned_graph, graph_mapper):
        """ Get the payload of the command.  By default, this just returns the\
            payload in the packet, but this can be overridden to compute the\
            payload from the routing information if so required.  This will be\
            called after mapping, during data specification generation.

        :param routing_info: The routing information generated during mapping\
                    from which edge keys can be obtained
        :type routing_info: \
                    :py:class:`pacman.model.routing_info.routing_info.RoutingInfo`
        :param partitioned_graph: The partitioned graph for which the routing\
                    information was obtained
        :type partitioned_graph: \
                    :py:class:`pacman.model.partitioned_graph.partitioned_graph.PartitionedGraph`
        :param graph_mapper: The mapper between the partitioned and\
                    partitionable graphs
        :type graph_mapper: \
                    :py:class:`pacman.model.graph_mapper.graph_mapper.GraphMapper`
        :return: The payload of the command, or None if there is no payload
        :rtype: int
        """
        return self._payload

    def is_payload(self):
        """ Determine if this command has a payload.  By default, this returns\
            True if the payload passed in to the constructor is not None, but\
            this can be overridden to indicate that a payload will be\
            generated, despite None being passed to the constructor

        :return: True if there is a payload, False otherwise
        :rtype: bool
        """
        return self._payload is not None
