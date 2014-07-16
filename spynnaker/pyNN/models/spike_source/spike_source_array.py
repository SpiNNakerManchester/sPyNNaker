import os
import math

from pacman103.lib import lib_map, data_spec_gen, data_spec_constants
from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.core.utilities import packet_conversions
from pacman103.core.spinnman.scp import scamp
from pacman103.core import exceptions
import numpy
import struct
from math import ceil

import logging
logger = logging.getLogger(__name__)

# Identifier for this application (may contain institution 
# and specific application information - format to be decided):
SYSTEM_REGION         = 1
BLOCK_INDEX_REGION    = 2
SPIKE_DATA_REGION     = 3
SPIKE_HISTORY_REGION  = 4

RECORD_SPIKE_BIT = 1<<0

SETUP_SZ = 16
BITS_PER_WORD = 32.0
BLOCK_INDEX_HEADER_WORDS = 3
BLOCK_INDEX_ROW_WORDS = 2

# Version string for this DSG:
DsgVersionMaj = 0
DsgVersionMin = 1

RECORD_SPIKE_BIT = 1<<0

INFINITE_SIMULATION = 4294967295

class SpikeSourceArray(ComponentVertex):
    """
    COMMENT ME

    """
    core_app_identifier = data_spec_constants.SPIKESOURCEARRAY_CORE_APPLICATION_ID
    
    def __init__(self, atoms, constraints=None, label="SpikeSourceArray", 
            spike_times=[]):
        """
        Creates a new SpikeSourceArray Object.
        """
        super( SpikeSourceArray, self ).__init__(
            n_neurons = atoms,
            constraints = constraints,
            label = label
        )
        self.spike_times = spike_times

    @property
    def model_name( self ):
        """
        Return a string representing a label for this class.
        """
        return "SpikeSourceArray"
    
    def get_maximum_atoms_per_core(self):
        return 256
    
    
    def getSpikesPerTimestep(self, lo_atom, hi_atom, machineTimeStep):
        """
        spikeArray is a list with one entry per 'neuron'. The entry for
        one neuron is a list of times (in ms) when the neuron fires.
        We need to transpose this 'matrix' and get a list of firing neuron
        indices for each time tick:
        List can come in two formats (both now supported):
        1) Official PyNN format - single list that is used for all neurons
        2) SpiNNaker format - list of lists, one per neuron
        """
        spikeDict = dict()
        if isinstance(self.spike_times[0], list):
            # This is in SpiNNaker 'list of lists' format:
            for neuron in range(lo_atom, hi_atom + 1):
                for timeStamp in self.spike_times[neuron]:
                    timeStampInTicks = int((timeStamp * 1000.0) / machineTimeStep)
                    if timeStampInTicks not in spikeDict.keys():
                        spikeDict[timeStampInTicks] = [neuron]
                    else:
                        spikeDict[timeStampInTicks].append(neuron)
        else:
            # This is in official PyNN format, all neurons use the same list:
            neuronList = range(lo_atom, hi_atom + 1)
            for timeStamp in self.spike_times:
                timeStampInTicks = int((timeStamp * 1000.0) / machineTimeStep)
                if timeStampInTicks not in spikeDict.keys():
                    spikeDict[timeStampInTicks] = neuronList
                else:
                    spikeDict[timeStampInTicks].append(neuronList)

        return spikeDict
    
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
        
        if no_machine_time_steps is None:
            return 0
        
        OUT_SPIKE_BYTES = int(ceil((hi_atom - lo_atom + 1) / 32.0)) * 4
        return self.get_recording_region_size(no_machine_time_steps,
                OUT_SPIKE_BYTES)
    
    def getBlockIndexBytes(self, no_active_timesteps):
        return (BLOCK_INDEX_HEADER_WORDS + (no_active_timesteps 
                * BLOCK_INDEX_ROW_WORDS)) * 4
                
    def getSDRAMUse(self, lo_atom, hi_atom, no_machine_time_steps, 
            machine_time_step_us):
        spikeDict = self.getSpikesPerTimestep(lo_atom, hi_atom, 
                machine_time_step_us)
        no_active_timesteps = len(spikeDict.keys())
        spikeBlockRowLength = self.getSpikeBlockRowLength(
                ((hi_atom - lo_atom) + 1))
        spikeRegionSz = self.getSpikeRegionBytes(spikeBlockRowLength, 
                no_active_timesteps)
        blockIndexRegionSize = self.getBlockIndexBytes(no_active_timesteps)
        spikeHistoryRegionSz = self.getSpikeBufferSize(lo_atom, hi_atom, 
                no_machine_time_steps)
        return (SETUP_SZ + spikeRegionSz + blockIndexRegionSize 
                + spikeHistoryRegionSz)
        
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
        single SpikeSource Array on one core.
        """
        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor, dao)
        spec.initialise(self.core_app_identifier, dao)               # User specified identifier

        spec.comment("\n*** Spec for SpikeSourceArray Instance ***\n\n")

        # Define lists to hold information on files to load and memory to write
        # in support of this application:

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        executableTarget = lib_map.ExecutableTarget(dao.get_common_binaries_directory()
                         + os.sep + 'spike_source_array.aplx',x, y, p)
        
        # ###################################################################
        # Reserve SDRAM space for memory areas:

        spec.comment("\nReserving memory space for spike data region:\n\n")

        machineTimeStep = dao.machineTimeStep # usec per simulation tick
        no_machine_time_steps = int((dao.run_time * 1000.0) / machineTimeStep)
        numNeurons, tableEntries, spikeBlocks, spikeRegionSize  =  \
                    self.processSpikeArrayInfo(subvertex, machineTimeStep)
        if spikeRegionSize == 0:
            spikeRegionSize = 4

        # Calculate memory requirements:
        blockIndexRegionSize = self.getBlockIndexBytes(len(tableEntries))
        spikeHistoryRegionSz = self.getSpikeBufferSize(subvertex.lo_atom, 
                subvertex.hi_atom, no_machine_time_steps)

        # Create the data regions for the spike source array:
        self.reserveMemoryRegions(spec, SETUP_SZ, blockIndexRegionSize,
                                  spikeRegionSize, spikeHistoryRegionSz)
        self.writeSetupInfo(spec, subvertex, spikeHistoryRegionSz)
        self.writeBlockIndexRegion(spec, subvertex, numNeurons, tableEntries)
        self.writeSpikeDataRegion(spec, numNeurons, spikeBlocks)
    
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

    def processSpikeArrayInfo(self, subvertex, machineTimeStep):
        """
        Parse python definitons of the required spike arrays and construct
        both the spike blocks, containing lists of spike IDs for each time step,
        and the index table, which gives the address in memory to access 
        the spike block for the current time step.
        """
        spikeDict = self.getSpikesPerTimestep(subvertex.lo_atom, 
                subvertex.hi_atom, machineTimeStep)
        
        # Dict spikeDict now has entries based on timeStamp and each entry
        # is a list of neurons firing at that time.
        # Get keys in time order:
        timeKeys = spikeDict.keys()
        timeKeys.sort()

        # Calculate how big the spike rows will be:
        spikeBlockRowLength = self.getSpikeBlockRowLength(subvertex.n_atoms)
        spikeRegionSize = self.getSpikeRegionBytes(spikeBlockRowLength, 
                len(timeKeys))
        
        # Create a new tableEntry for each unique time stamp, then
        # build a spike Block, tracking its size:
        tableEntries = list()
        spikeBlocks = list()
        spikeBlockStartAddr = 0
        for timeStamp in timeKeys:
            currentSpikeBlock = list()
            # Create tableEntry:
            tableEntries.append([timeStamp, spikeBlockStartAddr])
            # Construct spikeBlock:
            listOfSpikeIndices = spikeDict[timeStamp]
            for spikeIndex in listOfSpikeIndices:
                currentSpikeBlock.append(spikeIndex - subvertex.lo_atom)
            # Add the spike block for this time step to the spike blocks list:
            spikeBlocks.append(currentSpikeBlock)
            spikeBlockStartAddr += spikeBlockRowLength
        return subvertex.n_atoms, tableEntries, spikeBlocks, spikeRegionSize

    def reserveMemoryRegions(self, spec, setupSz, blockIndexRegionSize, 
                         spikeRegionSize, spikeHistBuffSz):
        """
        *** Modified version of same routine in models.py These could be 
        combined to form a common routine, perhaps by passing a list of 
        entries. ***
        Reserve memory for the system, indices and spike data regions.
        The indices region will be copied to DTCM by the executable.
        """
        spec.reserveMemRegion(region = SYSTEM_REGION, 
                                size = setupSz,
                               label = 'systemInfo')

        spec.reserveMemRegion(region = BLOCK_INDEX_REGION, 
                                size = blockIndexRegionSize, 
                               label = 'SpikeBlockIndexRegion')

        spec.reserveMemRegion(region = SPIKE_DATA_REGION, 
                                size = spikeRegionSize, 
                               label = 'SpikeDataRegion')
        if spikeHistBuffSz > 0:
            spec.reserveMemRegion(region = SPIKE_HISTORY_REGION,    
                size = spikeHistBuffSz,  label = 'spikeHistBuffer',
                leaveUnfilled = True)
        return

    def writeSetupInfo(self, spec, subvertex, spikeHistoryRegionSz):
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
        # What recording commands were set for the parent abstract_population.py?
        recordingInfo = 0
        if (spikeHistoryRegionSz > 0) and (self._record):
            recordingInfo |= RECORD_SPIKE_BIT
        recordingInfo = recordingInfo | 0xBEEF0000
        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region = SYSTEM_REGION)
        spec.write(data = recordingInfo)
        spec.write(data = spikeHistoryRegionSz)
        spec.write(data = 0)
        spec.write(data = 0)
        return

    def writeBlockIndexRegion(self, spec, subvertex, numNeurons, tableEntries):
        """
        Spike block index table. Gives address of each block of spikes.
        numNeurons is the total number of spike sources to be modelled.
        tableEntries is a list of the entries, each of which consists of:
        struct {
            uint32 timeStamp          # In simulation ticks
            uint32 addressOfBlockWord # Relative to start of spikeDataRegion
        } entry
        
        """
        spec.switchWriteFocus(region = BLOCK_INDEX_REGION)
        # Word 0 is the key (x, y, p) for this core:
        chipX, chipY, chipP = subvertex.placement.processor.get_coordinates()
        populationIdentity = \
            packet_conversions.get_key_from_coords(chipX, chipY, chipP)
        spec.write(data = populationIdentity)
 
        # Word 1 is the total number of 'neurons' (i.e. spike sources) in
        # the abstract_population.py:
        spec.write(data = numNeurons)

        # Word 2 is the total number of entries in this table of indices:
        numEntries = len(tableEntries)
        spec.write(data = numEntries)
        
        # Write individual entries:
        for entry in tableEntries:
            timeStamp = entry[0]   # Time in ticks when this block is used
            address   = entry[1]   # Address into spikeBlock region
            spec.write(data = timeStamp)
            spec.write(data = address)
        return

    def writeSpikeDataRegion(self, spec, numNeurons, spikeBlocks):
        """
        Spike data blocks.
        Blocks given in list spikeBlocks.
        Each block is a list of the indices of 'neurons' that should
        fire this tick of the simulation clock. they are converted
        into bit vectors of length ceil(numNeurons/32) words, in 
        which the bit position is the neuron index and a '1' in a given
        position means that neuron fires this tick.
        """
        spec.switchWriteFocus(region = SPIKE_DATA_REGION)
        vectorLen = int(math.ceil(numNeurons/32.0))
        for block in spikeBlocks:
            spikeBitVectors = [0] * vectorLen
            # Process this block of spike indices, setting a bit corresponding
            # to this index for each spiking neuron source:
            for index in block:
                wordNum = index >> 5
                bitNum = index & 0x1F
                orMask = 1<<bitNum
                # Set the target bit:
                spikeBitVectors[wordNum] = spikeBitVectors[wordNum] | orMask
            # Write this to spikeBlock region:
            for i in range(vectorLen):
                spec.write(data = spikeBitVectors[i])
           
        return
    
    def getSpikes(self, controller, runtime, compatible_output=False):
        # Spike sources store spike vectors optimally so calculate min words to represent
        subVertexOutSpikeBytesFunction = lambda subvertex : int(ceil(subvertex.n_atoms / 32.0)) * 4
        
        # Use standard behaviour to read spikes
        return self._getSpikes(controller, compatible_output,
                               SPIKE_HISTORY_REGION, subVertexOutSpikeBytesFunction, runtime)



