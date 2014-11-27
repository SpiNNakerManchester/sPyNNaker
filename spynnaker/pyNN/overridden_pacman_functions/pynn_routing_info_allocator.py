from pacman.model.constraints.key_allocator_routing_constraint import \
    KeyAllocatorRoutingConstraint
from pacman.model.routing_info.subedge_routing_info import SubedgeRoutingInfo
from pacman.operations.routing_info_allocator_algorithms import \
    BasicRoutingInfoAllocator
from pacman.utilities import utility_calls
from pacman import exceptions


class PyNNRoutingInfoAllocator(BasicRoutingInfoAllocator):
    
    def __init__(self):
        BasicRoutingInfoAllocator.__init__(self)
        self._supported_constraints.append(KeyAllocatorRoutingConstraint)

    #inhirrted from AbstractRoutingInfoAllocatorAlgorithm
    def _allocate_subedge_key_mask(self, out_going_subedge, placement):
        """helper method (can be overlaoded by future impliemntations of key
        alloc

        :param out_going_subedge: the outgoing subedge from a given subvert
        :param placement: the placement for the given subvert
        :type out_going_subedge: pacman.model.partitioned_graph.subegde.PartitionedEdge
        :type placement: pacman.model.placements.placement.Placement
        :return: a subedge_routing_info which contains the key, and mask of the\
         subvert
         :rtype: pacman.model.routing_info.subegde_rotuing_info.SubedgeRoutingInfo
         :raise None: does not raise any known exceptions
        """
        router_constraints = \
            utility_calls.locate_constraints_of_type(
                constraints=placement.subvertex.constraints,
                constraint_type=KeyAllocatorRoutingConstraint)
        if len(router_constraints) == 0:
            return BasicRoutingInfoAllocator._allocate_subedge_key_mask(
                self, out_going_subedge, placement)
        elif len(router_constraints) > 1:
            raise exceptions.PacmanRouteInfoAllocationException(
                "cannot determine how to reduce more than one router_constraint"
                "please reduce the constraints and try again, or use another"
                "routing info allocator")
        else:
            key, mask = \
                router_constraints[0].key_function_call(out_going_subedge)
            subedge_routing_info = SubedgeRoutingInfo(
                key=key, mask=mask, subedge=out_going_subedge,
                key_with_atom_ids_function=
                router_constraints[0].key_with_atom_ids_function_call)
            #check for storage of masks
            self.check_masks(mask, key, placement.subvertex)
            return subedge_routing_info