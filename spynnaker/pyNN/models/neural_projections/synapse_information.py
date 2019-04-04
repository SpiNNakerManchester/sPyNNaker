class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """
    __slots__ = [
        "_connector",
        "_index",
        "_synapse_dynamics",
        "_synapse_type",
        "_weight",
        "_delay"]

    def __init__(self, connector, synapse_dynamics, synapse_type,
                 weight=None, delay=None):
        self._connector = connector
        self._synapse_dynamics = synapse_dynamics
        self._synapse_type = synapse_type
        self._index = 0
        self._weight = weight
        self._delay = delay

    @property
    def connector(self):
        return self._connector

    @property
    def synapse_dynamics(self):
        return self._synapse_dynamics

    @property
    def synapse_type(self):
        return self._synapse_type

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    @property
    def weight(self):
        return self._weight

    @property
    def delay(self):
        return self._delay
