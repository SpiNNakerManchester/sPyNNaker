from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod

@add_metaclass(ABCMeta)
class AbstractRecordableVertex(object):

    def __init__(self):
        pass

    @abstractmethod
    def get_runtime_sdram_usage_for_atoms(
            self, vertex_slice, partitionable_graph, no_machine_time_steps):
        """
        a interface for pacman algorithms to deduce how much memory is used
        by a vertex during the runtime
        :param vertex_slice: the atom slice
        :param partitionable_graph: the partitionable graph
        :param no_machine_time_steps: the number of machine time steps
        :return: A sdram usage for the number of atoms, and machine time steps
        :rtype: int
        """