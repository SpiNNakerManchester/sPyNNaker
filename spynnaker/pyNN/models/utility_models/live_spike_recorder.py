import os

from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from spynnaker.pyNN.models.abstract_models.abstract_iptagable_vertex import \
    AbstractIPTagableVertex
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.models.abstract_models.abstract_data_specable_vertex \
    import AbstractDataSpecableVertex
from spynnaker.pyNN.utilities.conf import config
from pacman.model.constraints.placer_chip_and_core_constraint \
    import PlacerChipAndCoreConstraint
from data_specification.data_specification_generator import \
    DataSpecificationGenerator


class LiveSpikeRecorder(
    AbstractDataSpecableVertex, AbstractPartitionableVertex,
    AbstractIPTagableVertex):
    CORE_APP_IDENTIFIER = constants.APP_MONITOR_CORE_APPLICATION_ID
    SYSTEM_REGION = 0

    """
    A AbstractConstrainedVertex for the Monitoring application spikes and
    forwarding them to the host

    """
    def __init__(self, machine_time_step, tag, port, address):
        """
        Creates a new AppMonitor Object.
        """
        AbstractDataSpecableVertex.__init__(self, n_atoms=1,
                                            label="Monitor",
                                            machine_time_step=machine_time_step)
        AbstractPartitionableVertex.__init__(self, n_atoms=1, label="Monitor",
                                             max_atoms_per_core=1)
        AbstractIPTagableVertex.__init__(self, tag, port, address)

        self.add_constraint(PlacerChipAndCoreConstraint(0, 0))

    @property
    def model_name(self):
        return "AppMonitor"

    def is_ip_tagable_vertex(self):
        return True

    def generate_data_spec(self, subvertex, placement, sub_graph, graph,
                           routing_info, hostname, graph_sub_graph_mapper,
                           report_folder):
        """
        Model-specific construction of the data blocks necessary to build a
        single Application Monitor on one core.
        """
        data_writer, report_writer = \
            self.get_data_spec_file_writers(
                placement.x, placement.y, placement.p, hostname, report_folder)

        spec = DataSpecificationGenerator(data_writer, report_writer)

        spec.comment("\n*** Spec for AppMonitor Instance ***\n\n")

        # Calculate the size of the tables to be reserved in SDRAM:
        setup_sz = 16

        # Declare random number generators and distributions:
        #self.writeRandomDistributionDeclarations(spec, dao)
        # Construct the data images needed for the Neuron:
        self.reserve_memory_regions(spec, setup_sz)
        self.write_setup_info(spec, subvertex, graph_sub_graph_mapper)

        # End-of-Spec:
        spec.end_specification()
        data_writer.close()

    def reserve_memory_regions(self, spec, setup_sz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(region=self.SYSTEM_REGION,
                                   size=setup_sz,
                                   label='setup')
        return

    def write_setup_info(self, spec, subvertex, graph_sub_graph_mapper):
        """
        Write information used to control the simulation and gathering of
        results. Currently, this means the flag word used to signal whether
        information on neuron firing and neuron potential is either stored
        locally in a buffer or passed out of the simulation for storage/display
        as the simulation proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
            Bit 1: Record neuron potential
            Bit 2: Record gsyn values
            Bit 3: Reserved
            Bit 4: Output spike history on-the-fly
            Bit 5: Output neuron potential
            Bit 6: Output spike rate
        """

        # Write this to the system region (to be picked up by the simulation):
        spec.switch_write_focus(region=self.SYSTEM_REGION)
        spec.write_value(data=self._machine_time_step)
        spec.write_value(data=self._no_machine_time_steps)

    def get_binary_file_name(self):
         # Rebuild executable name
        common_binary_path = os.path.join(config.get("SpecGeneration",
                                                     "common_binary_folder"))

        binary_name = os.path.join(common_binary_path,
                                   'live_spike_recorder.aplx')
        return binary_name

    #inherited from partitionable vertex
    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        return 0

    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        return 0

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        return 0
