from pacman.model.graphs.machine import MachineEdge
from pacman.model.partitioner_splitters import SplitterSliceLegacy
from spinn_utilities.overrides import overrides
from spynnaker.pyNN.extra_algorithms.splitter_components import (
    AbstractSpynnakerSplitterDelay)


class SpynnakerSplitterSliceLegacy(
        SplitterSliceLegacy, AbstractSpynnakerSplitterDelay):

    def __init__(self):
        SplitterSliceLegacy.__init__(self, "spynnaker_splitter_slice_legacy")
        AbstractSpynnakerSplitterDelay.__init__(self)

    @overrides(SplitterSliceLegacy.get_pre_vertices)
    def get_pre_vertices(self, edge, outgoing_edge_partition):
        extra_pre_edge_types = [MachineEdge]
        extra_pre_edge_types.extend(self.extra_pre_edge_type())
        return self._get_map(extra_pre_edge_types)

    @overrides(SplitterSliceLegacy.get_post_vertices)
    def get_post_vertices(
            self, edge, outgoing_edge_partition, src_machine_vertex):
        extra_pre_edge_types = [MachineEdge]
        extra_pre_edge_types.extend(self.extra_post_edge_type())
        return self._get_map(extra_pre_edge_types)
