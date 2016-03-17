
class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """

    def __init__(self, connector, synapse_dynamics, synapse_type):
        self._connector = connector
        self._synapse_dynamics = synapse_dynamics
        self._synapse_type = synapse_type
        self._index = 0

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
