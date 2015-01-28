from pacman.model.partitioned_graph.partitioned_vertex import PartitionedVertex


class PartitionedPopulationVertex(PartitionedVertex):

    def __init__(self, n_atoms, resources_required, label,
                 constraints=None):
        PartitionedVertex.__init__(self, resources_required=resources_required,
                                   label=label, constraints=constraints)
        self._n_atoms = n_atoms