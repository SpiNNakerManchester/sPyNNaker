from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex
from spinn_front_end_common.interface.provenance\
    .provides_provenance_data_from_machine_impl \
    import ProvidesProvenanceDataFromMachineImpl

from enum import Enum


class DelayExtensionPartitionedVertex(
        PartitionedVertex, ProvidesProvenanceDataFromMachineImpl):

    _DELAY_EXTENSION_REGIONS = Enum(
        value="DELAY_EXTENSION_REGIONS",
        names=[('SYSTEM', 0),
               ('DELAY_PARAMS', 1),
               ('PROVENANCE_REGION', 2)])

    def __init__(self, resources_required, label, constraints=None):
        PartitionedVertex.__init__(
            self, resources_required, label, constraints=constraints)
        ProvidesProvenanceDataFromMachineImpl.__init__(
            self, self._DELAY_EXTENSION_REGIONS.PROVENANCE_REGION.value, 0)
