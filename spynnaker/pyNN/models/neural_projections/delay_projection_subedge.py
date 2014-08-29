from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_properties.synaptic_list import SynapticList
from spynnaker.pyNN.models.neural_properties.synapse_row_info \
    import SynapseRowInfo
from spynnaker.pyNN import exceptions

import logging
logger = logging.getLogger(__name__)


class DelayProjectionSubedge(ProjectionPartitionedEdge):
    
    def __init__(self, edge, presubvertex, postsubvertex, associated_edge):
        ProjectionPartitionedEdge.__init__(self, presubvertex, postsubvertex,
                                           associated_edge)
        
        self.synapse_sublist = None
        self.synapse_delay_rows = None
    
    def get_synapse_sublist(self):
        """
        Gets the synapse list for this subedge
        """
        if self.synapse_sublist is None:
            
            synapse_sublist = \
                self._associated_edge.get_synaptic_data().get_atom_sublist(
                    self._pre_subvertex.lo_atom, self._pre_subvertex.hi_atom,
                    self._post_subvertex.lo_atom, self._post_subvertex.hi_atom)
            
            if logger.isEnabledFor("debug"):
                logger.debug("Original Synapse List rows:")
                for i in range(len(synapse_sublist)):
                    logger.debug("{}: {}".format(i, synapse_sublist[i]))
        
            if len(synapse_sublist) > 256:
                raise exceptions.SynapticMaxIncomingAtomsSupportException(
                    "Delay sub-vertices can only support up to 256 incoming"
                    " neurons!")
                
            full_delay_list = list()
            for i in range(0, self._associated_edge.num_delay_stages):
                min_delay = (i * self._associated_edge.max_delay_per_neuron)
                max_delay = \
                    min_delay + self._associated_edge.max_delay_per_neuron
                delay_list =  \
                    self._associated_edge.get_synaptic_data()\
                        .get_delay_sublist(min_delay, max_delay)
                
#                 if logger.isEnabledFor("debug"):
#                     logger.debug("    Rows for delays {} - {}:".format(
#                             min_delay, max_delay))
#                     for i in range(len(delay_list)):
#                         logger.debug("{}: {}".format(i, delay_list[i]))
                
                full_delay_list.extend(delay_list)
                
                # Add extra rows for the "missing" items, up to 256
                if (i + 1) < self._associated_edge.num_delay_stages:
                    for _ in range(0, 256 - len(delay_list)):
                        full_delay_list.append(SynapseRowInfo([], [], [], []))
            self.synapse_sublist = SynapticList(full_delay_list)
            self.synapse_delay_rows = len(full_delay_list)
        return self.synapse_sublist
    
    def get_synaptic_data(self, spinnaker, delay_offset):
        delay_list = self._post_subvertex.vertex.get_synaptic_data(
            spinnaker, self._pre_subvertex, self.synapse_delay_rows,
            self._post_subvertex,
            self._associated_edge.synapse_row_io).get_rows()
        rows = list()
        for pre_atom in range(0, self._pre_subvertex.n_atoms):
            rows.append(SynapseRowInfo([], [], [], []))
        
        for i in range(0, self._associated_edge.num_delay_stages):
            min_delay = \
                (i * self._associated_edge.max_delay_per_neuron) + delay_offset
            list_offset = i * 256
            for pre_atom in range(0, self._pre_subvertex.n_atoms):
                row = delay_list[list_offset + pre_atom]
                rows[pre_atom].append(row, min_delay=min_delay)
        return SynapticList(rows)
    
    def free_sublist(self):
        """
        Indicates that the list will not be needed again
        """
        self.synapse_sublist = None
