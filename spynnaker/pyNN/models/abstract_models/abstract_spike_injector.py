from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.models.abstract_models.abstract_reverse_iptagable_vertex import \
    AbstractReverseIPTagableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from abc import ABCMeta
from six import add_metaclass

@add_metaclass(ABCMeta)
class AbstractSpikeInjector(
    AbstractRecordableVertex, AbstractDataSpecableVertex,
    AbstractPartitionableVertex, AbstractReverseIPTagableVertex):

    CORE_APP_IDENTIFER = constants.