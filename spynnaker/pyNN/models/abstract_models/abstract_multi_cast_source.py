from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from abc import ABCMeta
from six import add_metaclass


@add_metaclass(ABCMeta)
class AbstractMultiCastSource(
        AbstractRecordableVertex, AbstractDataSpecableVertex,
        AbstractPartitionableVertex):

    def __init__(self, machine_time_step):
        """
        constructor that depends upon the Component vertex
        """
        AbstractRecordableVertex.__init__(self, machine_time_step,
                                          "multi_cast_source_sender")
        AbstractDataSpecableVertex.__init__(self, n_atoms=1,
                                            label="multi_cast_source_sender",
                                            machine_time_step=machine_time_step)
        AbstractPartitionableVertex.__init__(
            self, label="multi_cast_source_sender", n_atoms=1,
            max_atoms_per_core=1)

