import os
import numpy
from pacman103.core.utilities import packet_conversions
from pacman103.lib import lib_map, data_spec_gen, data_spec_constants
from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.front.common.randomDistributions import generateParameter
from math import exp, ceil
from pacman103.core import exceptions
from pacman103.core.spinnman.scp import scamp
import struct

import logging
logger = logging.getLogger(__name__)

# Identifier for this application (may contain institution 
# and specific application information - format to be decided):

# Version string for this DSG:
DsgVersionMaj = 0
DsgVersionMin = 1

SYSTEM_REGION              = 1
POISSON_PARAMS_REGION      = 2
SPIKE_HISTORY_REGION       = 3

SLOW_RATE_PER_TICK_CUTOFF = 0.25

SETUP_SZ = 16
PARAMS_BASE_WORDS = 3
PARAMS_WORDS_PER_NEURON = 5
RANDOM_SEED_WORDS = 4

RECORD_SPIKE_BIT = 1<<0

INFINITE_SIMULATION = 4294967295

class SpikeSourcePoisson(ComponentVertex):
    """
    This class represents a Poisson Spike source object, which can represent
    a abstract_population.py of virtual neurons each with its own parameters.
    """
    core_app_identifier = data_spec_constants.SPIKESOURCEPOISSON_CORE_APPLICATION_ID

    def __init__(self, atoms, contraints=None, label="SpikeSourcePoisson",
            rate = 1, start = 0, duration = 10000, seed=None):
        """
        Creates a new SpikeSourcePoisson Object.
        """
        super( SpikeSourcePoisson, self ).__init__(
            n_neurons = atoms,
            constraints = contraints,
            label = label
        )
        
        self.rate = rate
        self.start = start
        self.duration = duration
        self.seed = seed

    @property
    def model_name(self):
        """
        Return a string representing a label for this class.
        """
        return "SpikeSourcePoisson"
    
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
    
    def getParamsBytes(self, lo_atom, hi_atom):
        """
        Gets the size of the possion parameters in bytes
        """
        return (RANDOM_SEED_WORDS + PARAMS_BASE_WORDS 
                + (((hi_atom - lo_atom) + 1) * PARAMS_WORDS_PER_NEURON)) * 4

    def get_cpu(self, lo_atom, hi_atom):
        '''
        buffer method for cpu calculations for a collection of atoms
        '''
        # TODO needs to be correct from here
        no_atoms = hi_atom - lo_atom + 1
        return 128 * no_atoms

    def get_DTCM(self, lo_atom, hi_atom):
        '''
        buffer method for dtcm calculations for a collection of atoms
        '''
        # TODO needs to be correct from here
        no_atoms = hi_atom - lo_atom + 1
        return (44 + (16 * 4)) * no_atoms

    def get_SDRAM(self, lo_atom, hi_atom, no_machine_time_steps):
        '''
        buffer method for sdram calculations for a collection of atoms
        '''
        # TODO needs to be correct from here
        poissonParamsSz      = self.getParamsBytes(lo_atom, hi_atom)
        spikeHistBuffSz     = self.getSpikeBufferSize(lo_atom, hi_atom, 
                no_machine_time_steps)
        return SETUP_SZ + poissonParamsSz + spikeHistBuffSz

    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
                                machine_time_step_us, partition_data_object):
        '''
        returns the seperate resource requirements for a range of atoms
        in a resource object with a assumption object that tracks any
        assumptions made by the model when estimating resource requirement
        '''
        cpu_cycles = self.get_cpu(lo_atom, hi_atom)
        dtcm_requirement = self.get_DTCM(lo_atom, hi_atom)
        sdram_requirment = self.get_SDRAM(lo_atom, hi_atom, 
                no_machine_time_steps)
        return lib_map.Resources(cpu_cycles, dtcm_requirement, sdram_requirment)
        
    def get_maximum_atoms_per_core(self):
        '''
        returns the maxiumum number of atoms that a core can support
        for this model
        '''
        return 256

    def generateDataSpec(self, processor, subvertex, dao):
        """
        Model-specific construction of the data blocks necessary to build a
        single SpikeSourcePoisson on one core.
        """
        # Get simulation information:
        machineTimeStep  = dao.machineTimeStep
        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor, dao)
        spec.initialise(self.core_app_identifier, dao)  # User-specified identifier

        spec.comment("\n*** Spec for SpikeSourcePoisson Instance ***\n\n")

        # Load the expected executable to the list of load targets for this core
        # and the load addresses:
        x, y, p = processor.get_coordinates()
        executableTarget = \
            lib_map.ExecutableTarget(dao.get_common_binaries_directory() +
                                     os.sep + 'spike_source_poisson.aplx',x,
                                     y, p)
        
        # Get parameters about the group of neurons living on this core:
        # How many are there?:
        no_machine_time_steps = int((dao.run_time * 1000.0) / dao.machineTimeStep)
        x,y,p               = processor.get_coordinates()
        poissonParamsSz      = self.getParamsBytes(subvertex.lo_atom, 
                subvertex.hi_atom)
        spikeHistBuffSz     = self.getSpikeBufferSize(subvertex.lo_atom, 
                subvertex.hi_atom, no_machine_time_steps)
        
        # Reserve SDRAM space for memory areas:
        self.reserveMemoryRegions(spec, SETUP_SZ, poissonParamsSz,
                                                 spikeHistBuffSz)

        # Write region 1 (system information on buffer size, etc);
        self.writeSetupInfo(spec, subvertex, spikeHistBuffSz)

        self.writePoissonParameters(spec, machineTimeStep, processor,
                                          subvertex.n_atoms)

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
        loadTargets = list()

        # Return list of executables, load files:
        return  executableTarget, loadTargets, memoryWriteTargets

    def reserveMemoryRegions(self, spec, setupSz, poissonParamsSz, \
                                                  spikeHistBuffSz):
        """
        Reserve memory regions for poisson source parameters
        and output buffer.
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region = SYSTEM_REGION,              \
                                size = setupSz,                    \
                               label = 'setup')
        spec.reserveMemRegion(region = POISSON_PARAMS_REGION,       \
                                size = poissonParamsSz,             \
                               label = 'PoissonParams')
        if spikeHistBuffSz > 0:
            spec.reserveMemRegion(region = SPIKE_HISTORY_REGION,    \
                size = spikeHistBuffSz,  label = 'spikeHistBuffer',     \
                leaveUnfilled = True)

    def writeSetupInfo(self, spec, subvertex, spikeHistoryRegionSz):
        """
        Write information used to control the simulationand gathering of results.
        Currently, this means the flag word used to signal whether information on
        neuron firing and neuron potential is either stored locally in a buffer or
        passed out of the simulation for storage/display as the simulation proceeds.

        The format of the information is as follows:
        Word 0: Flags selecting data to be gathered during simulation.
            Bit 0: Record spike history
        """

        # What recording commands wereset for the parent abstract_population.py?
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

    def writePoissonParameters(self, spec, machineTimeStep, processor, 
            numNeurons):
        """
        Generate Neuron Parameter data for Poisson spike sources (region 2):
        """
        spec.comment("\nWriting Neuron Parameters for %d poisson sources:\n"
                % numNeurons)

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switchWriteFocus(region = POISSON_PARAMS_REGION)

        # Write header info to the memory region:
        
        # Write Key info for this core:
        chipX, chipY, chipP = processor.get_coordinates()
        populationIdentity = \
            packet_conversions.get_key_from_coords(chipX, chipY, chipP)
        spec.write(data = populationIdentity)
        
        # Write the random seed (4 words), generated randomly!
        if self.seed == None:
            spec.write(data = numpy.random.randint(0x7FFFFFFF))
            spec.write(data = numpy.random.randint(0x7FFFFFFF))
            spec.write(data = numpy.random.randint(0x7FFFFFFF))
            spec.write(data = numpy.random.randint(0x7FFFFFFF))
        else:
            spec.write(data = self.seed[0])
            spec.write(data = self.seed[1])
            spec.write(data = self.seed[2])
            spec.write(data = self.seed[3])
        
        # For each neuron, get the rate to work out if it is a slow
        # or fast source
        slow_sources = list()
        fast_sources = list()
        for i in range(0, numNeurons):
            
            # Get the parameter values for source i:
            rateVal     = generateParameter(self.rate, i)
            startVal    = generateParameter(self.start, i)
            endVal      = generateParameter(self.duration, i) + startVal
            
            # Decide if it is a fast or slow source and 
            spikesPerTick = (float(rateVal) * (machineTimeStep / 1000000.0))
            if spikesPerTick <= SLOW_RATE_PER_TICK_CUTOFF:
                slow_sources.append([i, rateVal, startVal, endVal])
            else:
                fast_sources.append([i, spikesPerTick, startVal, endVal])
                
        # Write the numbers of each type of source
        spec.write(data = len(slow_sources))
        spec.write(data = len(fast_sources))

        # Now write one struct for each slow source as follows 
        #
        #   typedef struct slow_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #      
        #     accum mean_isi_ticks;
        #     accum time_to_spike_ticks;
        #   } slow_spike_source_t;
        for (neuronId, rateVal, startVal, endVal) in slow_sources:
            isiValScaled = int(float(1000000.0 / (rateVal * machineTimeStep)) 
                    * 32768.0)
            startScaled   = int(startVal  * 1000.0 / machineTimeStep)
            endScaled     = int(endVal    * 1000.0 / machineTimeStep)
            spec.write(data = neuronId,       sizeof='uint32')
            spec.write(data = startScaled,    sizeof='uint32')
            spec.write(data = endScaled,      sizeof='uint32')
            spec.write(data = isiValScaled,   sizeof='s1615')
            spec.write(data = 0x0,            sizeof='uint32')
        
        # Now write 
        #   typedef struct fast_spike_source_t
        #   {
        #     uint32_t neuron_id;
        #     uint32_t start_ticks;
        #     uint32_t end_ticks;
        #     
        #     unsigned long fract exp_minus_lambda;
        #   } fast_spike_source_t;
        for (neuronId, spikesPerTick, startVal, endVal) in fast_sources:
            exp_minus_lamda = exp(-1.0 * spikesPerTick)
            exp_minus_lamda_scaled = int(exp_minus_lamda * float(0xFFFFFFFF))
            startScaled   = int(startVal  * 1000.0 / machineTimeStep)
            endScaled     = int(endVal    * 1000.0 / machineTimeStep)
            spec.write(data = neuronId,       sizeof='uint32')
            spec.write(data = startScaled,    sizeof='uint32')
            spec.write(data = endScaled,      sizeof='uint32')
            spec.write(data = exp_minus_lamda_scaled,   sizeof='u032')
        return
    
    def getSpikes(self, controller, runtime, compatible_output=False):
        # Spike sources store spike vectors optimally so calculate min words to represent
        subVertexOutSpikeBytesFunction = lambda subvertex : int(ceil(subvertex.n_atoms / 32.0)) * 4
        
        # Use standard behaviour to read spikes
        return self._getSpikes(controller, compatible_output,
                               SPIKE_HISTORY_REGION, subVertexOutSpikeBytesFunction, runtime)



