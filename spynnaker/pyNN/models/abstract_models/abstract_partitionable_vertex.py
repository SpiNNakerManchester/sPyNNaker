from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.resources.cpu_cycles_per_tick_resource import \
    CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.graph.vertex import Vertex


@add_metaclass(ABCMeta)
class AbstractPartitionableVertex(Vertex):

    def __init__(self, n_atoms, label, constraints=None):
        Vertex.__init__(self, n_atoms, label, constraints)

    @abstractmethod
    def get_sdram_usage_for_atoms(self, lo_atom, hi_atom):
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

    def get_resources_used_by_atoms(self, lo_atom, hi_atom):
        """
        returns the seperate resource requirements for a range of atoms
        in a resource object with a assumption object that tracks any
        assumptions made by the model when estimating resource requirement
        """
        cpu_cycles = self.get_cpu_usage_for_atoms(lo_atom, hi_atom)
        dtcm_requirement = self.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
        sdram_requirment = self.get_sdram_usage_for_atoms(lo_atom, hi_atom)
        resources = list()
        # noinspection PyTypeChecker
        resources.append(CPUCyclesPerTickResource(cpu_cycles))

        # noinspection PyTypeChecker
        resources.append(DTCMResource(dtcm_requirement))

        # noinspection PyTypeChecker
        resources.append(SDRAMResource(sdram_requirment))
        return resources