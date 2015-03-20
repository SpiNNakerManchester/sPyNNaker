from enum import Enum
from data_specification.data_specification_generator import \
    DataSpecificationGenerator

from pacman.model.partitionable_graph.abstract_partitionable_vertex import \
    AbstractPartitionableVertex

from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities import constants


class ReInjectionVertex(AbstractPartitionableVertex,
                        AbstractDataSpecableVertex):
    """ class to support the re-injection of dropped routing packets to attempt
     to stop deadlocks

    """

    MAX_ATOMS_PER_VERTEX = 1
    _RE_INJECTION_REGIONS = Enum(
        value="RE_INJECTION_REGIONS",
        names=[('SYSTEM', 0)])

    def __init__(self, machine_time_step, timescale_factor,
                 constraints=None, label="reinjection_vertex"):
        AbstractPartitionableVertex.__init__(
            self, self.MAX_ATOMS_PER_VERTEX, label, self.MAX_ATOMS_PER_VERTEX)
        AbstractDataSpecableVertex.__init__(
            self, self.MAX_ATOMS_PER_VERTEX, label,
            machine_time_step, timescale_factor, constraints=None)

    def get_binary_file_name(self):
        return "re_injection.aplx"

    def model_name(self):
        return "reinjection_vertex"

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        return 200000

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        return 2 ** 15

    def generate_data_spec(self, subvertex, placement, sub_graph, graph,
                           routing_info, hostname, graph_subgraph_mapper,
                           report_folder):
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)
        spec.reserve_memory_region(
            region=self._RE_INJECTION_REGIONS.SYSTEM.value,
            size=constants.SETUP_SIZE, label='setup')

        self._write_basic_setup_info(spec,
                                     constants.RE_INJECTOR_CORE_APPLICATION_ID)
        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        return 2 * 4 #timescalefactor and machine_time_step (each a uint32)