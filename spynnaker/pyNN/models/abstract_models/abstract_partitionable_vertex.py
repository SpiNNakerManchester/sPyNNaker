from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.graph.vertex import Vertex
from pacman.model.constraints.partitioner_maximum_size_constraint \
    import PartitionerMaximumSizeConstraint
from pacman.model.resources.resource_container import ResourceContainer

import sys
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPartitionableVertex(Vertex):

    def __init__(self, n_atoms, label, max_atoms_per_core, constraints=None):
        Vertex.__init__(self, n_atoms, label, constraints)
        #add the max atom per core constraint
        max_atom_per_core_constraint = \
            PartitionerMaximumSizeConstraint(max_atoms_per_core)
        self.add_constraint(max_atom_per_core_constraint)

    @abstractmethod
    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        """
        method for calculating sdram usage
        """

    @abstractmethod
    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        """
        method for caulculating dtcm usage for a coltection of atoms
        """

    @abstractmethod
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        """
        Gets the CPU requirements for a range of atoms
        """

    def get_resources_used_by_atoms(self, lo_atom, hi_atom, vertex_in_edges):
        """
        returns the seperate resource requirements for a range of atoms
        in a resource object with a assumption object that tracks any
        assumptions made by the model when estimating resource requirement
        """
        cpu_cycles = self.get_cpu_usage_for_atoms(lo_atom, hi_atom)
        dtcm_requirement = self.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
        sdram_requirment = \
            self.get_sdram_usage_for_atoms(lo_atom, hi_atom, vertex_in_edges)
        # noinspection PyTypeChecker
        resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                      dtcm=DTCMResource(dtcm_requirement),
                                      sdram=SDRAMResource(sdram_requirment))
        return resources

    def get_max_atoms_per_core(self):
        """
        returns the max atom per core possible given the constraints set on
        this vertex
        """
        current_found_max_atoms_per_core = sys.maxint
        for constraint in self.constraints:
            if (isinstance(constraint, PartitionerMaximumSizeConstraint) and
                    constraint.size <= current_found_max_atoms_per_core):
                current_found_max_atoms_per_core = constraint.size
        return current_found_max_atoms_per_core