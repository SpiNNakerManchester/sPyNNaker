from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.models.abstract_models.abstract_reverse_iptagable_vertex import \
    AbstractReverseIPTagableVertex
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractSpikeInjector(
        AbstractRecordableVertex, AbstractDataSpecableVertex,
        AbstractPartitionableVertex, AbstractReverseIPTagableVertex):

    def __init__(self, machine_time_step, timescale_factor, tag, port, address):
        """
        constructor that depends upon the Component vertex
        """
        AbstractRecordableVertex.__init__(
            self, machine_time_step, "multi_cast_source_sender")
        AbstractDataSpecableVertex.__init__(
            self, n_atoms=1, label="multi_cast_source_sender",
            machine_time_step=machine_time_step,
            timescale_factor=timescale_factor)
        AbstractPartitionableVertex.__init__(
            self, label="multi_cast_source_sender", n_atoms=1,
            max_atoms_per_core=1)
        AbstractReverseIPTagableVertex.__init__(self, tag, port, address)

    def is_reverse_ip_tagable_vertex(self):
        return True

    @abstractmethod
    def is_spike_injecotr(self):
        """ helper emthod for is_instance
        :return:
        """
