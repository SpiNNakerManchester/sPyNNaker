
class SynapseInformation(object):
    """ Contains the synapse information including the connector, synapse type\
        and synapse dynamics
    """
    __slots__ = [
        "__connector",
        "__index",
        "__synapse_dynamics",
        "__synapse_type"]

    def __init__(self, connector, synapse_dynamics, synapse_type):
        self.__connector = connector
        self.__synapse_dynamics = synapse_dynamics
        self.__synapse_type = synapse_type
        self.__index = 0

    @property
    def connector(self):
        return self.__connector

    @property
    def synapse_dynamics(self):
        return self.__synapse_dynamics

    @property
    def synapse_type(self):
        return self.__synapse_type

    @property
    def index(self):
        return self.__index

    @index.setter
    def index(self, index):
        self.__index = index
