import logging

from spynnaker.pyNN.projections.projection_partitioned_edge\
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.common.abstract_filterable_edge\
    import AbstractFilterableEdge


logger = logging.getLogger(__name__)


class DelayAfferentPartitionedEdge(ProjectionPartitionedEdge,
                                   AbstractFilterableEdge):

    def __init__(self, edge, presubvertex, presubvertex_slice, postsubvertex,
                 postsubvertex_slice, constraints):
        ProjectionPartitionedEdge.__init__(
            self, edge, presubvertex, presubvertex_slice, postsubvertex,
            postsubvertex_slice, constraints)
        AbstractFilterableEdge.__init__(self)

    def filter_sub_edge(self):
        """
        """
        if ((self._presubvertex_slice.lo_atom !=
                self._postsubvertex_slice.lo_atom) or
            (self._presubvertex_slice.hi_atom !=
                self._postsubvertex_slice.hi_atom)):
            return True
        return False
