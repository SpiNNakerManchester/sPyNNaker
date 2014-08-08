from pacman.model.graph.edge import Edge
from spynnaker.pyNN.models.neural_projections.projection_subedge import \
    ProjectionSubedge
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    fixed_synapse_row_io import FixedSynapseRowIO
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN.utilities.conf import config
import logging
logger = logging.getLogger(__name__)


class ProjectionEdge(Edge):
    
    def __init__(self, prevertex, postvertex, machine_time_step,
                 connector=None, synapse_list=None, synapse_dynamics=None,
                 label=None):
        Edge.__init__(self, prevertex, postvertex, label=label)
        self._connector = connector
        self._synapse_dynamics = synapse_dynamics
        self._synapse_list = synapse_list
        self._synapse_row_io = FixedSynapseRowIO()
        
        # If the synapse_list was not specified, create it using the connector
        if connector is not None and synapse_list is None:
            self._synapse_list = \
                connector.generate_synapse_list(prevertex, postvertex,
                                                1000.0 / machine_time_step)
        
        # If there are synapse dynamics for this connector, create a plastic
        # synapse list
        if synapse_dynamics is not None:
            self._synapse_row_io = synapse_dynamics.get_synapse_row_io()
    
    def create_subedge(self, presubvertex, postsubvertex, label=None):
        """
        Creates a subedge from this edge
        """
        return ProjectionSubedge(presubvertex, postsubvertex, self)
        
    def filter_sub_edge(self, subedge):
        """
        Method is called to allow a given sub-edge to prune itself if it
        serves no purpose.
        :return: True if the partricular sub-edge can be pruned, and
        False otherwise.
        """
        return not self._synapse_list.is_connected(
            subedge.presubvertex.lo_atom, subedge.presubvertex.hi_atom,
            subedge.postsubvertex.lo_atom, subedge.postsubvertex.hi_atom)

    def get_max_n_words(self, lo_atom=None, hi_atom=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param lo_atom: The start of the range of atoms in 
                                   the subvertex (default is first atom)
        :param hi_atom: The end of the range of atoms in 
                                   the subvertex (default is last atom)
        """
        return max([self._synapse_row_io.get_n_words(synapse_row, lo_atom,
                                                     hi_atom)
                    for synapse_row in self._synapse_list.get_rows()])
        
    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        return self._synapse_list.get_n_rows()
    
    def get_synapse_row_io(self):
        """
        Gets the row reader and writer
        """
        return self._synapse_row_io

    def get_synaptic_data(self, spinnaker=None):
        """
        Get synaptic data for all connections in this Projection.
        if spinnaker == None, then just return the one stored in memory via
         self._synapse_list
        """
        logger.debug("Reading synapse data for edge between {} and {}"
                    .format(self._pre_vertex.label, self._post_vertex.label))

        #if theres no spinnaker, assume your looking at the internal one here.
        if spinnaker is None:
            return self._synapse_list

        sub_graph = spinnaker.sub_graph
        min_delay = config.get("Model", "min_delay")
        if sub_graph is None:
            return self._synapse_list
        else:
            sorted_subedges = \
                sorted(sub_graph.get_subedges_from_edge(self),
                       key=lambda sub_edge:
                       (sub_edge.presubvertex.lo_atom,
                        sub_edge.postsubvertex.lo_atom))

            synaptic_list = list()
            last_pre_lo_atom = None
            for subedge in sorted_subedges:
                if subedge.pruneable:
                    rows = [SynapseRowInfo([], [], [], [])
                            for _ in range(subedge.presubvertex.n_atoms)]
                else:
                    rows =\
                        subedge.get_synaptic_data(spinnaker,
                                                  min_delay).get_rows()
                if (last_pre_lo_atom is None) or \
                        (last_pre_lo_atom != subedge.presubvertex.lo_atom):
                    synaptic_list.extend(rows)
                    last_pre_lo_atom = subedge.presubvertex.lo_atom
                else:
                    for i in range(len(rows)):
                        row = rows[i]
                        synaptic_list[i + last_pre_lo_atom]\
                            .append(row, lo_atom=subedge.postsubvertex.lo_atom)

            return SynapticList(synaptic_list)

    @property
    def synapse_dynamics(self):
        return self._synapse_dynamics