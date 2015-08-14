from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex

from spinn_front_end_common.abstract_models.abstract_data_specable_partitioned_vertex import AbstractDataSpecablePartitionedVertex
from spinn_front_end_common.interface.has_n_machine_timesteps import HasNMachineTimesteps
from spinn_front_end_common.abstract_models.abstract_outgoing_edge_same_contiguous_keys_restrictor import AbstractOutgoingEdgeSameContiguousKeysRestrictor
from spinn_front_end_common.abstract_models.abstract_executable import AbstractExecutable

from spynnaker.pyNN.models.neuron.abstract_population_recordable_subvertex \
    import AbstractPopulationRecordableSubvertex


class PartitionedPopulationVertex(
        PartitionedVertex, AbstractPopulationRecordableSubvertex,
        AbstractDataSpecablePartitionedVertex, HasNMachineTimesteps,
        AbstractOutgoingEdgeSameContiguousKeysRestrictor, AbstractExecutable):

    def __init__(self, resources_required, label, constraints=None):
        PartitionedVertex.__init__(self, resources_required, label,
                                   constraints=constraints)
        AbstractPopulationRecordableSubvertex.__init__(self)
        AbstractDataSpecablePartitionedVertex.__init__(self)
