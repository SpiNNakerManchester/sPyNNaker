
class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """

    def __init__(self, connector, synapse_dynamics, synapse_type):
        self._connector = connector
        self._synapse_dynamics
        self._synapse_type
        self._row_offsets = None

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
    def row_offsets(self):
        return self._row_offsets

    @row_offsets.getter
    def row_offsets(self, row_offsets):
        self._row_offsets = row_offsets
