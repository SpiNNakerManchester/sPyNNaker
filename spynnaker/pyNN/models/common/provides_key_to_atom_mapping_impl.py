from pacman.executor.injection_decorator import inject_items
from spinn_front_end_common.abstract_models.\
    abstract_provides_key_to_atom_mapping import \
    AbstractProvidesKeyToAtomMapping
from pacman.model.decorators.overrides import overrides


class ProvidesKeyToAtomMappingImpl(AbstractProvidesKeyToAtomMapping):

    def __init__(self):
        pass

    @inject_items({
        "graph_mapper": "MemoryGraphMapper"
    })
    @overrides(
        AbstractProvidesKeyToAtomMapping.routing_key_partition_atom_mapping,
        additional_arguments={"graph_mapper"})
    def routing_key_partition_atom_mapping(
            self, routing_info, partition, graph_mapper):
        mapping = list()
        vertex_slice = graph_mapper.get_slice(partition.pre_vertex)
        keys = routing_info.get_keys(vertex_slice.n_atoms)
        atom = vertex_slice.lo_atom
        for key in keys:
            mapping.append((atom, key))
            atom += 1
        return mapping