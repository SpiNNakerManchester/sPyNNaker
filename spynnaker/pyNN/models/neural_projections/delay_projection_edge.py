'''
Created on 09 April 2014

@author: knightj
'''
from pacman103.core import exceptions
from pacman103 import conf
from pacman103.front.common.projection_edge import ProjectionEdge
from pacman103.front.common.delay_projection_subedge import DelayProjectionSubedge

import logging
logger = logging.getLogger(__name__)

class DelayProjectionEdge(ProjectionEdge):

    DELAY_PAGE_SIZE = 256
    
    def __init__(self, prevertex, postvertex, machine_time_step, 
            num_delay_stages, max_delay_per_neuron, connector=None, 
            synapse_list=None, constraints=None, synapse_dynamics=None,
            label=None):
        super(DelayProjectionEdge, self).__init__(prevertex, postvertex, 
                machine_time_step, connector=connector, 
                synapse_list=synapse_list, constraints=constraints, 
                synapse_dynamics=synapse_dynamics, label=label)
        self.num_delay_stages = num_delay_stages
        self.max_delay_per_neuron = max_delay_per_neuron
        
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
        n_atoms = self.prevertex.get_maximum_atoms_per_core()
        if self.prevertex.custom_max_atoms_per_core != None:
            n_atoms = self.prevertex.custom_max_atoms_per_core
        if self.prevertex.atoms < n_atoms:
            n_atoms = self.prevertex.atoms
        if n_atoms > 100:
            n_atoms = 100
        return ((self.synapse_list.get_n_rows() / n_atoms) 
            * self.DELAY_PAGE_SIZE * self.num_delay_stages)
    
    def create_subedge(self, presubvertex, postsubvertex):
        """
        Creates a subedge from this edge
        """
        return DelayProjectionSubedge(self, presubvertex, postsubvertex)
