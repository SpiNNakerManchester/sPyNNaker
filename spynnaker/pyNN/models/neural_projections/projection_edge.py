'''
Created on 25 Mar 2014

@author: zzalsar4
'''
from pacman103.lib.graph.edge import Edge
from pacman103.front.common.projection_subedge import ProjectionSubedge
from pacman103.front.common.fixed_synapse_row_io import FixedSynapseRowIO
from pacman103.front.common.synaptic_list import SynapticList

import logging, numpy, struct
from pacman103.front.common.synapse_row_info import SynapseRowInfo
logger = logging.getLogger(__name__)

class ProjectionEdge(Edge):
    
    def __init__(self, prevertex, postvertex, machine_time_step,
            connector=None, synapse_list=None,
            synapse_dynamics=None, constraints=None, label=None):
        super(ProjectionEdge, self).__init__(prevertex, postvertex, 
                constraints=constraints, label=label)
        self.connector = connector
        self.synapse_dynamics = synapse_dynamics

        self.synapse_list = synapse_list
        self.synapse_row_io = FixedSynapseRowIO()
        
        # If the synapse_list was not specified, create it using the connector
        if connector is not None and synapse_list is None:
            self.synapse_list = connector.generate_synapse_list(prevertex,
                    postvertex, 1000.0 / machine_time_step)
        
        # If there are synapse dynamics for this connector, create a plastic
        # synapse list
        if synapse_dynamics is not None:
            self.synapse_row_io = synapse_dynamics.get_synapse_row_io()
    
    def create_subedge(self, presubvertex, postsubvertex):
        """
        Creates a subedge from this edge
        """

        return ProjectionSubedge(self, presubvertex, postsubvertex)
        
    def filterSubEdge(self, subedge):
        """
        Method is called to allow a given sub-edge to prune itself if it
        serves no purpose.
        :return: True if the partricular sub-edge can be pruned, and
        False otherwise.
        """
        return self.synapse_list.is_connected(subedge.presubvertex.lo_atom,
                                              subedge.presubvertex.hi_atom,
                                              subedge.postsubvertex.lo_atom,
                                              subedge.postsubvertex.hi_atom)\
               == False

    def get_max_n_words(self, lo_atom=None, hi_atom=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param lo_atom: The start of the range of atoms in 
                                   the subvertex (default is first atom)
        :param hi_atom: The end of the range of atoms in 
                                   the subvertex (default is last atom)
        """
        return max([self.synapse_row_io.get_n_words(synapse_row, lo_atom, 
                hi_atom) for synapse_row in self.synapse_list.get_rows()])
        
    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        return self.synapse_list.get_n_rows()
    
    def get_synapse_row_io(self):
        """
        Gets the row reader and writer
        """
        return self.synapse_row_io
    

    def get_synaptic_data(self, controller, min_delay):
        '''
        Get synaptic data for all connections in this Projection.
        '''
        logger.info("Reading synapse data for edge between {} and {}".format(
                self.prevertex.label, self.postvertex.label))
        sorted_subedges = sorted(self.subedges, 
                key = lambda subedge: (subedge.presubvertex.lo_atom,
                                       subedge.postsubvertex.lo_atom))
        
        synaptic_list = list()
        last_pre_lo_atom = None
        for subedge in sorted_subedges:
            rows = None
            if subedge.pruneable:
                rows = [SynapseRowInfo([], [], [], []) 
                        for _ in range(subedge.presubvertex.n_atoms)]
            else:
                rows = subedge.get_synaptic_data(controller, min_delay).get_rows()
            if (last_pre_lo_atom is None) or (last_pre_lo_atom 
                    != subedge.presubvertex.lo_atom):
                synaptic_list.extend(rows)
                last_pre_lo_atom = subedge.presubvertex.lo_atom
            else:
                for i in range(len(rows)):
                    row = rows[i]
                    synaptic_list[i + last_pre_lo_atom].append(row, 
                            lo_atom=subedge.postsubvertex.lo_atom)
                        
                
        return SynapticList(synaptic_list)
