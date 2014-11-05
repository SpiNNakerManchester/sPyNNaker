from abc import ABCMeta
from six import add_metaclass

from spynnaker.pyNN.models.abstract_models.abstract_population_recordable_vertex import \
    AbstractPopulationRecordableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spinn_front_end_common.abstract_models.abstract_reverse_iptagable_vertex import \
    AbstractReverseIPTagableVertex
from spinn_front_end_common.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex


@add_metaclass(ABCMeta)
class AbstractSpikeInjector(
        AbstractPopulationRecordableVertex, AbstractDataSpecableVertex,
        AbstractPartitionableVertex, AbstractReverseIPTagableVertex):

    def __init__(self, machine_time_step, tag, port, address):
        """
        constructor that depends upon the Component vertex
        """
        AbstractPopulationRecordableVertex.__init__(
            self, machine_time_step, "multi_cast_source_sender")
        AbstractDataSpecableVertex.__init__(self,
                                            label="multi_cast_source_sender",
                                            machine_time_step=machine_time_step)
        AbstractPartitionableVertex.__init__(
            self, label="multi_cast_source_sender", n_atoms=1,
            max_atoms_per_core=1)
        AbstractReverseIPTagableVertex.__init__(self, tag, port, address)

    def is_reverse_ip_tagable_vertex(self):
        return True
