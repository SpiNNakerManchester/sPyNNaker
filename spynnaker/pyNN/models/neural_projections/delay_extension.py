
from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.models.abstract_models.abstract_component_vertex \
    import AbstractComponentVertex
from spynnaker.pyNN.models.neural_projections.delay_projection_edge import \
    DelayProjectionEdge

from math import ceil
from enum import Enum
import copy
import os
import math
import logging


logger = logging.getLogger(__name__)

_DELAY_EXTENSION_REGIONS = Enum(
    'SYSTEM',
    'DELAY_PARAMS',
    'SPIKE_HISTORY'
)


class DelayExtension(AbstractComponentVertex):
    """
    Instance of this class provide delays to incoming spikes in multiples
    of the maximum delays of a neuron (typically 16 or 32)
    """
    CORE_APP_IDENTIFIER = constants.DELAY_EXTENSION_CORE_APPLICATION_ID
    
    def __init__(self, n_neurons, max_delay_per_neuron, 
                 constraints=None, label="DelayExtension"):
        """
        Creates a new DelayExtension Object.
        """

        super( DelayExtension, self ).__init__(
            n_neurons = n_neurons,
            constraints = constraints,
            label = label
        )
        self.max_delay_per_neuron = max_delay_per_neuron

    @property
    def model_name( self ):
        """
        Return a string representing a label for this class.
        """
        return "DelayExtension"
    
    def get_maximum_atoms_per_core(self):
        return 256
    
    
    def getSpikesPerTimestep(self, lo_atom, hi_atom, machineTimeStep):
        """
        TODO: More accurate calculation of bounds
        """
        return 200
    
    def getSpikeBlockRowLength(self, n_atoms):
        return int(math.ceil(n_atoms / BITS_PER_WORD))
        
    def getSpikeRegionBytes(self, spikeBlockRowLength, no_active_timesteps):
        return spikeBlockRowLength * no_active_timesteps * 4
    
    def getSpikeBufferSize(self, lo_atom, hi_atom, no_machine_time_steps):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if self._record == False:
            return 0
        OUT_SPIKE_BYTES = int(ceil((hi_atom - lo_atom + 1) / 32.0)) * 4
        return self.get_recording_region_size(no_machine_time_steps,
                OUT_SPIKE_BYTES)
    
    def getBlockIndexBytes(self, no_active_timesteps):
        return (BLOCK_INDEX_HEADER_WORDS + (no_active_timesteps 
                * BLOCK_INDEX_ROW_WORDS)) * 4
                
    def getSDRAMUse(self, lo_atom, hi_atom, no_machine_time_steps, 
            machine_time_step_us):
        # TODO: Fill this in
        return 0
        
    def getDTCMUse(self, lo_atom, hi_atom):
        n_atoms = (hi_atom - lo_atom) + 1
        return (44 + (16 * 4)) * n_atoms
    
    def getCPUUse(self, lo_atom, hi_atom):
        n_atoms = (hi_atom - lo_atom) + 1
        return 128 * n_atoms
    
    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps, 
            machine_time_step_us, partition_data_object):
        cpu = self.getCPUUse(lo_atom, hi_atom)
        dtcm = self.getDTCMUse(lo_atom, hi_atom)
        sdram = self.getSDRAMUse(lo_atom, hi_atom, no_machine_time_steps, 
                machine_time_step_us)
        return lib_map.Resources(cpu, dtcm, sdram)

    def generateDataSpec(self, processor, subvertex, dao):
        """
        Model-specific construction of the data blocks necessary to build a
        single Delay Extension Block on one core.
        """
        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor, dao)
        spec.initialise(self.core_app_identifier, dao)               # User specified identifier

        spec.comment("\n*** Spec for Delay Extension Instance ***\n\n")

        # Define lists to hold information on files to load and memory to write
        # in support of this application:

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        executableTarget = lib_map.ExecutableTarget(dao.get_common_binaries_directory()
                         + os.sep + 'delay_extension.aplx',x, y, p)
        
        # ###################################################################
        # Reserve SDRAM space for memory areas:

        delay_params_header_words = 3
        n_atoms = subvertex.hi_atom - subvertex.lo_atom  + 1
        block_len_words = int(ceil(n_atoms / 32.0))
        num_delay_blocks, delay_blocks = self.get_delay_blocks(subvertex)
        delay_params_sz = 4 * (delay_params_header_words 
                + (num_delay_blocks * block_len_words))
        
        spikeHistoryRegionSz = 0

        # Reserve memory:
        spec.comment("\nReserving memory space for data regions:\n\n")

        spec.reserveMemRegion( region = REGIONS.SYSTEM,
                                 size = SETUP_SZ,
                                label = 'setup' )

        spec.reserveMemRegion( region = REGIONS.DELAY_PARAMS,
                                 size = delay_params_sz,
                                label = 'delay_params' )

        self.writeSetupInfo( spec, subvertex, spikeHistoryRegionSz)

        self.writeDelayParameters(spec, processor, subvertex, num_delay_blocks,
                delay_blocks) 

        # End-of-Spec:
        spec.endSpec()
        spec.closeSpecFile() 

        # No memory writes or loads required for this Data Spec:
        memoryWriteTargets = list()

        simulationTimeInTicks = INFINITE_SIMULATION
        if dao.run_time is not None:
            simulationTimeInTicks = int((dao.run_time * 1000.0) 
                    /  dao.machineTimeStep)
        user1Addr = 0xe5007000 + 128 * p + 116 # User1 location reserved for core p
        memoryWriteTargets.append(lib_map.MemWriteTarget(x, y, p, user1Addr,
                                                         simulationTimeInTicks))

        loadTargets        = list()

        # Return list of executables, load files:
        return  executableTarget, loadTargets, memoryWriteTargets

    def writeSetupInfo(self, spec, subvertex, spikeHistoryRegionSz):
        """
        """
        recordingInfo = 0
        if self._record == True:
            recordingInfo |= RECORD_SPIKE_BIT
        recordingInfo = recordingInfo | 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region = REGIONS.SYSTEM)
        spec.write(data = recordingInfo)
        spec.write(data = spikeHistoryRegionSz)
        spec.write(data = 0)
        spec.write(data = 0)
        
    def get_delay_blocks(self, subvertex):
        # Create empty list of words to fill in with delay data:
        num_words_per_row = int(ceil(subvertex.n_atoms / 32.0))
        one_block = [0] * num_words_per_row
        delay_block = list()
        num_delay_blocks = 0
        
        for subedge in subvertex.out_subedges:
            if not isinstance(subedge.edge, DelayProjectionEdge):
                raise Exception("One of the incoming subedges is not a subedge"
                        + " of a DelayAfferentEdge")
            if subedge.pruneable:
                continue
    
            # Loop through each possible delay block
            dest = subedge.postsubvertex
            #logger.debug("Examining delays from {} ({}-{}) to {} ({}-{}), prunable={}".format(
            #        subvertex.vertex.label, subvertex.lo_atom, subvertex.hi_atom,
            #        dest.vertex.label, dest.lo_atom, dest.hi_atom, 
            #        subedge.pruneable))
            synapse_list = subedge.edge.synapse_list.create_atom_sublist(
                  subvertex.lo_atom, subvertex.hi_atom, dest.lo_atom, 
                  dest.hi_atom)
            for b in range(MAX_DELAY_BLOCKS):
                min_delay = (b * self.max_delay_per_neuron) + 1
                max_delay = min_delay + self.max_delay_per_neuron
                delay_list = synapse_list.get_delay_sublist(min_delay,
                         max_delay)
                #if logger.isEnabledFor("debug"):
                #    logger.debug("Looking at delay stage {} ({} - {})".format(
                #        b, min_delay, max_delay))
                #    for i in range(len(delay_list)):n
                #        logger.debug("{}: {}".format(i, delay_list[i]))
                
                row_count = 0
                for row in delay_list:
                    if len(row.target_indices) != 0:
                        
                        # Fix the length of the list
                        num_delay_blocks = max(b + 1, num_delay_blocks)
                        while num_delay_blocks > len(delay_block):
                            delay_block.append(copy.copy(one_block))
                        
                        # This source neurons has synapses in the current delay
                        # range. So set the bit in the delay_block:
                        word_id = int(row_count / 32)
                        bit_id = row_count - (word_id * 32)
                        
                        #logger.debug("Adding delay for block {}, atom {}"
                        #        .format(b, row_count))
                        
                        delay_block[b][word_id] |= (1 << bit_id)
                    row_count += 1
                    
        return num_delay_blocks, delay_block

    def writeDelayParameters(self, spec, processor, subvertex, num_delay_blocks,
            delay_block):
        """
        Generate Delay Parameter data (region 2):
        """
        

        # Write spec with commands to construct required delay region:
        spec.comment("\nWriting Delay Parameters for %d Neurons:\n" 
                                               % subvertex.n_atoms)

        # Set the focus to the memory region 2 (delay parameters):
        spec.switchWriteFocus( region = REGIONS.DELAY_PARAMS )

        # Write header info to the memory region:
        # Write Key info for this core:
        chipX, chipY, chipP = processor.get_coordinates()
        populationIdentity = packet_conversions.get_key_from_coords(
                chipX, chipY, chipP)
        spec.write(data = populationIdentity)

        # Write the number of neurons in the block:
        spec.write(data = subvertex.n_atoms)

        # Write the number of blocks of delays:
        spec.write(data = num_delay_blocks)

        # Write the actual delay blocks
        for i in range(0, num_delay_blocks):
            spec.write_array(data = delay_block[i])
