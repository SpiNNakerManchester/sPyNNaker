from pacman.model.abstract_classes.abstract_partitionable_vertex import \
    AbstractPartitionableVertex
from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex

from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(
        AbstractRecordableVertex, AbstractPartitionableVertex):

    def __init__(self, label, n_neurons, constraints, max_atoms_per_core,
                 machine_time_step, timescale_factor):

        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_neurons, label=label, constraints=constraints,
            max_atoms_per_core=max_atoms_per_core)
        AbstractRecordableVertex.__init__(self, machine_time_step, label)

    @abstractmethod
    def retrieve_edge_constraints_for_senders(self):
        """

        :return:
        """

    @abstractmethod
    def retrieve_edge_constraints_for_receivers(self):
        """

        :return:
        """