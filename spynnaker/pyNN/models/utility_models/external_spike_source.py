from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.lib import lib_map
from pacman103.lib import data_spec_gen, data_spec_constants


import os

INFINITE_SIMULATION = 4294967295


class ExternalSpikeSource( ComponentVertex ):
    core_app_identifier = data_spec_constants.EXTERNAL_SPIKE_SOURCEE_CORE_APPLICATION_ID
    SYSTEM_REGION  = 1
    DATA_REGION =2

    """
    A Vertex for the Monitor application

    """

    def __init__(self, constraints = None, label ="External Spike Source"):
        """
        Creates a new AppMonitor Object.
        """
        super(ExternalSpikeSource , self ).__init__(
            n_neurons = 1,
            constraints = lib_map.VertexConstraints(x = 0, y = 0),
            label = label
        )


    @property
    def model_name(self):
        return "AppMonitor"

    def get_maximum_atoms_per_core(self):
        return 1

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
            machine_time_step_us, partition_data_object):
        return lib_map.Resources(0, 0, 0)

    def generateDataSpec(self, processor, subvertex, dao):
        """
        Model-specific construction of the data blocks necessary to build a
        single Application Monitor on one core.
        """
        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor, dao)
        spec.initialise(self.core_app_identifier, dao) # User specified identifier

        spec.comment("\n*** Spec for External Spike Source Instance ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        executableTarget = lib_map.ExecutableTarget(
                dao.get_common_binaries_directory() + os.sep
                     + 'external_spike_source.aplx', x, y, p)

        # Calculate the size of the tables to be reserved in SDRAM:
        setupSz           = 16  # Single word of info with flags, etc.
                                # plus the lengths of each of the output buffer
                                # regions in bytes

        # Declare random number generators and distributions:
        #self.writeRandomDistributionDeclarations(spec, dao)
        # Construct the data images needed for the Neuron:
        self.reserveMemoryRegions(spec, setupSz)
        self.writeSetupInfo(spec, subvertex)

        # End-of-Spec:
        spec.endSpec()
        spec.closeSpecFile()

        # No memory writes required for this Data Spec:
        memoryWriteTargets = list()
        simulationTimeInTicks = INFINITE_SIMULATION
        if dao.run_time is not None:
            simulationTimeInTicks = int((dao.run_time * 1000.0)
                    /  dao.machineTimeStep)
        user1Addr = 0xe5007000 + 128 * p + 116 # User1 location reserved for core p
        memoryWriteTargets.append(lib_map.MemWriteTarget(x, y, p, user1Addr,
                                                         simulationTimeInTicks))
        loadTargets = list()

        # Return list of executables, load files:
        return  executableTarget, loadTargets, memoryWriteTargets

    def reserveMemoryRegions(self, spec, setupSz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region = self.SYSTEM_REGION,              \
                                size = setupSz,                    \
                               label = 'setup')
        spec.reserveMemRegion( region = self.DATA_REGION,
                               size = 4,
                               label = 'data_region' )
        return

    def writeSetupInfo(self, spec, subvertex):
        """
        Write information used to control the simulationand gathering of results.
        Currently, this means the flag word used to signal whether information on
        neuron firing and neuron potential is either stored locally in a buffer or
        passed out of the simulation for storage/display as the simulation proceeds.

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
        # What recording commands we reset for the parent population.py?
        recordingInfo = subvertex.vertex.flags
        recordingInfo = recordingInfo | 0xBEEF0000
        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region = self.SYSTEM_REGION)
        spec.write(data = recordingInfo)
        spec.switchWriteFocus(region = self.DATA_REGION)
        key = (int(subvertex.placement.processor.chip.get_coords()[0]) << 24 |
               int(subvertex.placement.processor.chip.get_coords()[1]) << 16 |
               int(subvertex.placement.processor.idx))
        spec.write(data = key)
        return
