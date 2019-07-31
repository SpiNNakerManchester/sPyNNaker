from spinn_utilities.overrides import overrides
from spinn_front_end_common.abstract_models import AbstractChangableAfterRun
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet)
from .poisson_source_vertex import PoissonSourceVertex


DEFAULT_MAX_ATOMS_PER_CORE = 64


class PoissonSourcePartition(
        AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
        SimplePopulationSettable):

    __slots__ = [
        "_n_atoms",
        "_application_vertices",
        "_n_partitions",
        "_offset"
    ]

    def __init__(self, n_neurons, constraints, label, rate, max_rate, start,
                 duration, seed, model, poisson_weight):

        self._n_atoms = n_neurons
        self._application_vertices = list()

        if self._n_atoms > DEFAULT_MAX_ATOMS_PER_CORE:
            self._n_partitions = 2
        else:
            self._n_partitions = 1

        self._offset = self._compute_partition_and_offset_size()

        for i in range(self._n_partitions):
            # Distribute neurons in order to have the low neuron cores completely filled
            atoms = self._offset if (self._n_atoms - (self._offset * (i + 1)) >= 0) \
                else self._n_atoms - (self._offset * i)

            self._application_vertices.append(PoissonSourceVertex(
                atoms, constraints, label + "_p" + str(i) + "_poisson_vertex", rate, max_rate, start,
                duration, seed, DEFAULT_MAX_ATOMS_PER_CORE, model, poisson_weight, self._offset*i))

    def get_application_vertices(self):
        return self._application_vertices

    def _compute_partition_and_offset_size(self):
        return -((-self._n_atoms / self._n_partitions) // DEFAULT_MAX_ATOMS_PER_CORE) * DEFAULT_MAX_ATOMS_PER_CORE

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        for p in range(self._n_partitions):
            self._application_vertices[p].mark_no_changes()

    @property
    def n_atoms(self):
        return self._n_atoms

    def read_parameters_from_machine(self, globals_variables):

        for p in range(self._n_partitions):
            machine_vertices = globals_variables.get_simulator().graph_mapper \
                .get_machine_vertices(self._application_vertices[p])

            # go through each machine vertex and read the parameters
            # it contains
            for machine_vertex in machine_vertices:
                # tell the core to rewrite params back to the
                # SDRAM space.
                placement = globals_variables.get_simulator().placements. \
                    get_placement_of_vertex(machine_vertex)

                self._application_vertices[p].read_parameters_from_machine(
                    globals_variables.get_simulator().transceiver, placement,
                    globals_variables.get_simulator().graph_mapper.get_slice(
                        machine_vertex))

    @property
    def out_vertices(self):
        return self._application_vertices
