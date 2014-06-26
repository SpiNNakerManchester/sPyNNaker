from pacman103.front.common.randomDistributions import RandomDistribution
from pacman103.front.common.component_vertex import ComponentVertex
from pacman103.front.common import enums

import pacman103.core.exceptions as exceptions
from pacman103.core.utilities.memory_utils import getAppDataBaseAddressOffset,\
                                                  getRegionBaseAddressOffset
from pacman103.front.common.synaptic_manager import SynapticManager
from pacman103.core.utilities import packet_conversions
from pacman103.core.spinnman.scp import scamp
from pacman103.lib import lib_map, data_spec_gen, data_spec_constants

import numpy
import struct
import os
import math
import ctypes
import logging
logger = logging.getLogger(__name__)

REGIONS = enums.enum1(
    'SYSTEM',
    'NEURON_PARAMS',
    'SYNAPSE_PARAMS',
    'ROW_LEN_TRANSLATION',
    'MASTER_POP_TABLE',
    'SYNAPTIC_MATRIX',
    'STDP_PARAMS',
    'SPIKE_HISTORY',
    'POTENTIAL_HISTORY',
    'GSYN_HISTORY',
)

# Some constants
SETUP_SIZE = 16 # Single word of info with flags, etc.
                # plus the lengths of each of the output buffer
                # regions in bytes

NO_PARAMS = 10  
PARAMS_HEADER_SIZE = 3 # Number of 32-bit words in header of params block
PARAMS_BASE_SIZE = 4 * (PARAMS_HEADER_SIZE + NO_PARAMS)

RECORD_SPIKE_BIT = 1<<0
RECORD_STATE_BIT = 1<<1
RECORD_GSYN_BIT  = 1<<2

# From neuron common-typedefs.h
SYNAPSE_INDEX_BITS = 8
MAX_NEURON_SIZE = (1 << SYNAPSE_INDEX_BITS)
OUT_SPIKE_SIZE = (MAX_NEURON_SIZE >> 5) # The size of each output spike line
OUT_SPIKE_BYTES = OUT_SPIKE_SIZE * 4 # The number of bytes for each spike line
V_BUFFER_SIZE_PER_TICK_PER_NEURON = 4
GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON = 4 

INFINITE_SIMULATION = 4294967295

#natively supported delays for all models
MAX_SUPPORTED_DELAY_TICS = 16

class PopulationVertex( ComponentVertex , SynapticManager):
    """
    Underlying Vertex model for Neural Populations.
    """
    
    def __init__(self, n_neurons, n_params, binary, constraints = None, 
            label = None):
        ComponentVertex.__init__(self, n_neurons = n_neurons,
                                 constraints = constraints,
                                 label = label)
        SynapticManager.__init__(self)

        
        self._n_params = n_params
        self._binary = binary
        
        self._record_v = False
        self._record_gsyn = False

        
    def record_v(self):
        self._record_v = True
    
    def record_gsyn(self):
        self._record_gsyn = True
    
    def writeRandomDistributionDeclarations( self, spec, dao ):
        """
        Write out declarations for all random number generators and 
        random distributions.
        """
        # logger.debug(dao.rngs)
        # logger.debug(dao.randDists)
        for key in dao.rngs:
            logger.debug("RNG index is ", key)

        for key in dao.randDists:
            logger.debug("Random dist index is ", key)

    def declareRNG( self, rngId = None, seed = 1 ):
        """
        If a specified random number generator has not yet been declared, do
        so. Info on which RNGs have been declared is held in the spec object,
        in a list called rngList.
        """
        if rngId == None:
            raise Exception(
                "ERROR: No index given in attempt to declare RNG."
            )

        if rngId < 0 or rngId > data_spec_constants.MAX_RNGS:
            raise Exception(
                "ERROR: Requested RNG index (%d) out of range." % rngId
            )

        if self.rngList[rngId] == False:
            # Write command to declare it:
            self.declareRNG(rngId = rngId, seed = seed)
            self.rngList[rngId] = True

    def declareRandomDistribution(self, distId = None, distParams = None):
        pass
    
    def getNeuronParamsSize(self, lo_atom, hi_atom):
        """
        Gets the size of the neuron parameters for a range of neurons
        """
        return PARAMS_BASE_SIZE + (4 * ((hi_atom - lo_atom) + 1) 
                * self._n_params)

    def getSDRAM(self, lo_atom, hi_atom, no_machine_time_steps):
        """
        Gets the SDRAM requirements for a range of atoms
        """
        
        return (SETUP_SIZE + self.getNeuronParamsSize(lo_atom, hi_atom)
            + self.getSynapseParameterSize(lo_atom, hi_atom)
            + self.getSTDPParameterSize(lo_atom, hi_atom, self.in_edges)
            + SynapticManager.ROW_LEN_TABLE_SIZE
            + SynapticManager.MASTER_POPULATION_TABLE_SIZE
            + self.getSynapticBlocksMemorySize(lo_atom, hi_atom, self.in_edges)
            + self.getSpikeBufferSize(lo_atom, hi_atom, no_machine_time_steps)
            + self.getVBufferSize(lo_atom, hi_atom, no_machine_time_steps)
            + self.getGSynBufferSize(lo_atom, hi_atom, no_machine_time_steps))
        
    def getDTCM(self, lo_atom, hi_atom):
        """
        Gets the DTCM requirements for a range of atoms
        """
        return (44 + (16 * 4)) * ((hi_atom - lo_atom) + 1)
    
    def getCPU(self, lo_atom, hi_atom):
        """
        Gets the CPU requirements for a range of atoms
        """
        raise NotImplementedError
    
    def get_resources_for_atoms(self, lo_atom, hi_atom, no_machine_time_steps,
            machine_time_step_us, partition_data_object):
        '''
        returns the seperate resource requirements for a range of atoms
        in a resource object with a assumption object that tracks any
        assumptions made by the model when estimating resource requirement
        '''
        cpu_cycles = self.getCPU(lo_atom, hi_atom)
        dtcm_requirement = self.getDTCM(lo_atom, hi_atom)
        sdram_requirment = self.getSDRAM(lo_atom, hi_atom, 
                no_machine_time_steps)
        return lib_map.Resources(cpu_cycles, dtcm_requirement, sdram_requirment)
        
    def getSpikeBufferSize(self, lo_atom, hi_atom, no_machine_time_steps):
        """
        Gets the size of the spike buffer for a range of neurons and time steps
        """
        if self._record == False:
            return 0
        
        if no_machine_time_steps is None:
            return 0
        
        return self.get_recording_region_size(no_machine_time_steps,
                OUT_SPIKE_BYTES)
    
    def getVBufferSize(self, lo_atom, hi_atom, no_machine_time_steps):
        """
        Gets the size of the v buffer for a range of neurons and time steps
        """
        if self._record_v == False:
            return 0
        
        return self.get_recording_region_size(no_machine_time_steps, 
                ((hi_atom - lo_atom) + 1) 
                     * V_BUFFER_SIZE_PER_TICK_PER_NEURON)
    
    def getGSynBufferSize(self, lo_atom, hi_atom, no_machine_time_steps):
        """
        Gets the size of the gsyn buffer for a range of neurons and time steps
        """
        if self._record_gsyn == False:
            return 0
        
        return self.get_recording_region_size(no_machine_time_steps, 
                ((hi_atom - lo_atom) + 1) 
                     * GSYN_BUFFER_SIZE_PER_TICK_PER_NEURON)

    def reserveMemoryRegions( self, spec, setupSz, neuronParamsSz,
                              synapseParamsSz, rowLenTransSz, masterPopTableSz,
                              allSynBlockSz, spikeHistBuffSz,
                              potentialHistBuffSz, gsynHistBuffSz,
                              stdpParamsSz ):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) Neuron parameter data (will be copied to DTCM by 'C' code at start-up)
        3) synapse parameter data (will be copied to DTCM)
        4) Synaptic row length look-up (copied to DTCM)
        5) Synaptic block look-up table. Translates the start address of each block 
           of synapses (copied to DTCM)
        6) Synaptic row data (lives in SDRAM)
        7) Spike history
        8) Neuron potential history
        9) Gsyn value history
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion( region = REGIONS.SYSTEM,
                               size = setupSz,
                               label = 'setup' )
        spec.reserveMemRegion( region = REGIONS.NEURON_PARAMS,
                               size = neuronParamsSz,
                               label = 'NeuronParams' )
        spec.reserveMemRegion( region = REGIONS.SYNAPSE_PARAMS,
                               size = synapseParamsSz,
                               label = 'SynapseParams' )
        spec.reserveMemRegion( region = REGIONS.ROW_LEN_TRANSLATION,
                               size = rowLenTransSz,
                               label = 'RowLenTable' )
        spec.reserveMemRegion( region = REGIONS.MASTER_POP_TABLE,
                               size = masterPopTableSz,
                               label = 'MasterPopTable' )
        spec.reserveMemRegion( region = REGIONS.SYNAPTIC_MATRIX,
                           size = allSynBlockSz,
                           label = 'SynBlocks' )

        if self._record:
            spec.reserveMemRegion( 
                region = REGIONS.SPIKE_HISTORY,
                size = spikeHistBuffSz,  
                label = 'spikeHistBuffer',
                leaveUnfilled = True 
            )

        if self._record_v:
            spec.reserveMemRegion(
                region = REGIONS.POTENTIAL_HISTORY,
                size = potentialHistBuffSz,
                label = 'potHistBuffer',
                leaveUnfilled = True
            )
        if self._record_gsyn:
            spec.reserveMemRegion(
                region = REGIONS.GSYN_HISTORY,
                size = gsynHistBuffSz,
                label = 'gsynHistBuffer',
                leaveUnfilled = True
            )
        if stdpParamsSz != 0:
            spec.reserveMemRegion( region = REGIONS.STDP_PARAMS,
                size = stdpParamsSz,
                label = 'stdpParams')

    def writeSetupInfo( self, spec, subvertex, spikeHistoryRegionSz,
                        neuronPotentialRegionSz, gsynRegionSz ):
        """
        Write information used to control the simulation and gathering of results.
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
        # What recording commands were set for the parent population.py?
        recordingInfo = 0
        if spikeHistoryRegionSz > 0 and self._record == True:
            recordingInfo |= RECORD_SPIKE_BIT
        if neuronPotentialRegionSz > 0 and self._record_v == True:
            recordingInfo |= RECORD_STATE_BIT
        if gsynRegionSz > 0 and self._record_gsyn == True:
            recordingInfo |= RECORD_GSYN_BIT
        recordingInfo = recordingInfo | 0xBEEF0000        

        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region = REGIONS.SYSTEM)
        spec.write(data = recordingInfo)
        spec.write(data = spikeHistoryRegionSz)
        spec.write(data = neuronPotentialRegionSz)
        spec.write(data = gsynRegionSz)
        
    def writeNeuronParameters(self, spec, machineTimeStep,
                              processor, subvertex, 
                              ring_buffer_to_input_left_shift):
        spec.comment("\nWriting Neuron Parameters for %d "
                     "Neurons:\n"%subvertex.n_atoms)

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switchWriteFocus( region = REGIONS.NEURON_PARAMS )

        # Write header info to the memory region:
        # Write Key info for this core:
        chipX, chipY, chipP = processor.get_coordinates()
        populationIdentity = \
            packet_conversions.get_key_from_coords(chipX, chipY, chipP)
        spec.write(data = populationIdentity)

        # Write the number of neurons in the block:
        spec.write(data = subvertex.n_atoms)

        # Write the number of parameters per neuron (struct size in words):
        params = self.get_parameters(machineTimeStep)
        spec.write(data = len( params ))

        # Write machine time step: (Integer, expressed in microseconds)
        spec.write(data = machineTimeStep)
        
        # Write ring_buffer_to_input_left_shift
        spec.write(data = ring_buffer_to_input_left_shift)
        
        # TODO: Took this out for now as I need random parameters
        # Create loop over number of neurons:
        #spec.loop(countReg = 15, startVal = 0, endVal = subvertex.n_atoms)
        for atom in range(0, subvertex.n_atoms):
            # Process the parameters
            for param in params:
                value = param.get_value()
                if (hasattr(value, "__len__")):
                    if len(value) > 1:
                        value = value[atom]
                    else:
                        value = value[0]
                
                datatype = param.get_datatype()
                scale = param.get_scale()

                value = value * scale

                if datatype == 's1615':
                    value = spec.doubleToS1615(value)
                elif datatype == 'uint32':
                    value = ctypes.c_uint32(value).value

                spec.write(data = value, sizeof=datatype)
        
        # TODO: See above
        # End the loop over the neurons:
        #spec.endLoop()
    
    def get_parameters(self, machineTimeStep):
        raise NotImplementedError
    
    def get_ring_buffer_to_input_left_shift(self, subvertex):
        total_exc_weights = numpy.zeros(subvertex.n_atoms)
        total_inh_weights = numpy.zeros(subvertex.n_atoms)
        for subedge in subvertex.in_subedges:
            sublist = subedge.get_synapse_sublist()
            sublist.sum_weights(total_exc_weights, total_inh_weights)
        
        max_weight = max((max(total_exc_weights), max(total_inh_weights)))
        max_weight_log_2 = 0
        if max_weight > 0:
            max_weight_log_2 = math.log(max_weight, 2)
        
        # Currently, we can only cope with positive left shifts, so the minimum
        # scaling will be no shift i.e. a max weight of 0nA
        if max_weight_log_2 < 0:
            max_weight_log_2 = 0
        
        max_weight_power = int(math.ceil(max_weight_log_2))
        
        logger.debug("Max weight is {}, Max power is {}".format(max_weight, 
                max_weight_power))
        
        # Actual shift is the max_weight_power - 1 for 16-bit fixed to s1615, 
        # but we ignore the "-1" to allow a bit of overhead in the above
        # calculation in case a couple of extra spikes come in 
        return max_weight_power
    
    def generateDataSpec( self, processor, subvertex, dao ):
        """
        Model-specific construction of the data blocks necessary to build a group
        of IF_curr_exp neurons resident on a single core.
        """
        # Get simulation information:
        machineTimeStep  = dao.machineTimeStep
        
        # Create new DataSpec for this processor:
        spec = data_spec_gen.DataSpec(processor, dao)
        spec.initialise(self.core_app_identifier, dao)  # User-specified identifier

        spec.comment("\n*** Spec for block of %s neurons ***\n" % (self.model_name))

        # Load the executable to the list of load targets for this core
        # and the load addresses:
        # TODO - AMMEND FOR BINARY SEARCH PATH IF DESIRED
        x, y, p = processor.get_coordinates()
        
        # Split binary name into title and extension
        binaryTitle, binaryExtension = os.path.splitext(self._binary)

        # If we have an STDP mechanism, add it's executable suffic to title
        if self._stdp_mechanism is not None:
            binaryTitle = binaryTitle + "_" + self._stdp_mechanism.get_vertex_executable_suffix()

        # Rebuild executable name
        binaryName = os.path.join(dao.get_common_binaries_directory(), binaryTitle + binaryExtension)

        executableTarget = lib_map.ExecutableTarget(
            binaryName,
            x, y, p
        )
        
        # Calculate the number of time steps
        no_machine_time_steps = int((dao.run_time * 1000.0) / machineTimeStep)
        
        x,y,p = processor.get_coordinates()
        
        # Calculate the size of the tables to be reserved in SDRAM:
        neuronParamsSz = self.getNeuronParamsSize(subvertex.lo_atom, 
                subvertex.hi_atom)
        synapseParamsSz = self.getSynapseParameterSize(subvertex.lo_atom, 
                subvertex.hi_atom)
        allSynBlockSz     = self.getExactSynapticBlockMemorySize(subvertex)
        spikeHistBuffSz = self.getSpikeBufferSize(subvertex.lo_atom, 
                subvertex.hi_atom, no_machine_time_steps)
        potentialHistBuffSz = self.getVBufferSize(subvertex.lo_atom, 
                subvertex.hi_atom, no_machine_time_steps)
        gsynHistBuffSz = self.getGSynBufferSize(subvertex.lo_atom, 
                subvertex.hi_atom, no_machine_time_steps)
        stdpRegionSz = self.getSTDPParameterSize(subvertex.lo_atom, 
                subvertex.hi_atom, self.in_edges)
        
        # Declare random number generators and distributions:
        self.writeRandomDistributionDeclarations(spec, dao)

        # Construct the data images needed for the Neuron:
        self.reserveMemoryRegions(spec, SETUP_SIZE, neuronParamsSz, 
                synapseParamsSz, SynapticManager.ROW_LEN_TABLE_SIZE,
                SynapticManager.MASTER_POPULATION_TABLE_SIZE, allSynBlockSz,
                spikeHistBuffSz, potentialHistBuffSz, gsynHistBuffSz,
                stdpRegionSz)

        self.writeSetupInfo(spec, subvertex, spikeHistBuffSz, 
                potentialHistBuffSz, gsynHistBuffSz)

        ring_buffer_shift = self.get_ring_buffer_to_input_left_shift(subvertex)
        weight_scale = self.get_weight_scale(ring_buffer_shift)
        logger.debug("Weight scale is {}".format(weight_scale))
        
        self.writeNeuronParameters(spec, machineTimeStep, processor, subvertex,
                ring_buffer_shift)

        self.writeSynapseParameters(spec, machineTimeStep, subvertex)
        
        self.writeSTDPParameters(spec, machineTimeStep, subvertex,
                                 weight_scale, REGIONS.STDP_PARAMS)

        self.writeRowLengthTranslationTable(spec, REGIONS.ROW_LEN_TRANSLATION)
        
        self.writeSynapticMatrixAndMasterPopulationTable(spec, subvertex, 
                                                         allSynBlockSz,
                                                         weight_scale,
                                                         REGIONS.MASTER_POP_TABLE,
                                                         REGIONS.SYNAPTIC_MATRIX)
        
        for subedge in subvertex.in_subedges:
            subedge.free_sublist()

        # End the writing of this specification:
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

        # Return list of target cores, executables, files to load and 
        # memory writes to perform:
        return  executableTarget, loadTargets, memoryWriteTargets
    
    def getSpikes(self, controller, runtime, compatible_output=False):
        if not controller.dao.has_ran:
            raise exceptions.PacmanException("The simulation has not yet ran,"
                                             "therefore spikes cannot be "
                                             "retrieved")
        # Spike sources store spike vectors optimally so calculate min words to represent
        subVertexOutSpikeBytesFunction = lambda subvertex : OUT_SPIKE_BYTES
        
        # Use standard behaviour to read spikes
        return self._getSpikes(controller, compatible_output, REGIONS.SPIKE_HISTORY,
                               subVertexOutSpikeBytesFunction, runtime)
    
    def get_neuron_parameter(self, region, compatible_output, controller):
        if not controller.dao.has_ran:
            raise exceptions.PacmanException("The simulation has not yet ran,"
                                             "therefore gsyn cannot be "
                                             "retrieved")
        value = numpy.zeros((0, 3))
        
        # Find all the sub-vertices that this population.py exists on
        for subvertex in self.subvertices:
            (x, y, p) = subvertex.placement.processor.get_coordinates()
            controller.txrx.select(x, y)
            
            # Get the App Data for the core
            appDataBaseAddressOffset = getAppDataBaseAddressOffset(p)
            appDataBaseAddressBuf = controller.txrx.memory_calls.read_mem(
                    appDataBaseAddressOffset, scamp.TYPE_WORD, 4)
            appDataBaseAddress = struct.unpack("<I", appDataBaseAddressBuf)[0]
            
            # Get the position of the value buffer
            vRegionBaseAddressOffset = getRegionBaseAddressOffset(
                    appDataBaseAddress, region)
            vRegionBaseAddressBuf = controller.txrx.memory_calls.read_mem(
                    vRegionBaseAddressOffset, scamp.TYPE_WORD, 4)
            vRegionBaseAddress = struct.unpack("<I", 
                    vRegionBaseAddressBuf)[0]
            vRegionBaseAddress += appDataBaseAddress
            
            # Read the size
            numberOfBytesWrittenBuf = controller.txrx.memory_calls.read_mem(
                    vRegionBaseAddress, scamp.TYPE_WORD, 4)
            numberOfBytesWritten = struct.unpack_from("<I", 
                    numberOfBytesWrittenBuf)[0]
                    
            # Read the values
            logger.debug("Reading %d (%s) bytes starting at %s" 
                    %(numberOfBytesWritten, hex(numberOfBytesWritten), 
                            hex(vRegionBaseAddress + 4)))
            vData = controller.txrx.memory_calls.read_mem(
                    vRegionBaseAddress + 4, scamp.TYPE_WORD, 
                    numberOfBytesWritten)
            bytesPerTimeStep = subvertex.n_atoms * 4
            numberOfTimeStepsWritten = numberOfBytesWritten / bytesPerTimeStep
            msPerTimestep = controller.dao.machineTimeStep / 1000.0
            
            logger.debug("Processing %d timesteps" % numberOfTimeStepsWritten)
            
            # Standard fixed-point 'accum' type scaling
            size = len(vData) / 4
            scale = numpy.zeros(size, dtype=numpy.float)
            scale.fill(float(0x7FFF))
            
            # Add an array for time and neuron id
            time = numpy.array([int(i / subvertex.n_atoms) * msPerTimestep 
                    for i in range(size)], dtype=numpy.float)
            neuronId = numpy.array([int(i % subvertex.n_atoms) 
                    + subvertex.lo_atom for i in range(size)], 
                    dtype=numpy.uint32)
            
            # Get the values
            tempValue = numpy.frombuffer(vData, dtype="<i4")
            tempValue = numpy.divide(tempValue, scale)
            tempArray = numpy.dstack((time, neuronId, tempValue))
            tempArray = numpy.reshape(tempArray, newshape=(-1, 3))
            
            value = numpy.append(value, tempArray, axis=0)
        
        logger.debug("Arranging parameter output")
        
        if compatible_output == True:
            
            # Change the order to be neuronID : time (don't know why - this
            # is how it was done in the old code, so I am doing it here too)
            value[:,[0,1,2]] = value[:,[1,0,2]]
            
            # Sort by neuron ID and not by time 
            vIndex = numpy.lexsort((value[:,2], value[:,1], value[:,0]))
            value = value[vIndex]
            return value
        
        # If not compatible output, we will sort by time (as NEST seems to do)
        vIndex = numpy.lexsort((value[:,2], value[:,1], value[:,0]))
        value = value[vIndex]
        return value
    
    def get_v(self, controller, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        logger.info("Getting v for %s" % (self.label))
        if not controller.dao.has_ran:
            raise exceptions.PacmanException("The simulation has not yet ran,"
                                             "therefore v cannot be "
                                             "retrieved")
        return self.get_neuron_parameter(REGIONS.POTENTIAL_HISTORY, 
                                         compatible_output, controller)


    def get_gsyn(self, controller, gather=True, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic conductances for recorded cells.

        """
        logger.info("Getting gsyn for %s" % (self.label))
        if not controller.dao.has_ran:
            raise exceptions.PacmanException("The simulation has not yet ran,"
                                             "therefore gsyn cannot be "
                                             "retrieved")
        return self.get_neuron_parameter(REGIONS.GSYN_HISTORY,
                                         compatible_output, controller)

    def get_synaptic_data(self, controller, presubvertex, pre_n_atoms,
                          postsubvertex, synapse_io):
        '''
        helper method to add other data for get weights via syanptic manager
        '''
        return SynapticManager._retrieve_synaptic_data(self, controller, presubvertex,
                                                  pre_n_atoms, postsubvertex,
                                                  REGIONS.MASTER_POP_TABLE,
                                                  synapse_io,
                                                  REGIONS.SYNAPTIC_MATRIX)

    def convert_param(self, param, no_atoms):
        '''
        converts parameters into numpy arrays as needed
        '''
        if isinstance(param, RandomDistribution):
            return numpy.asarray(param.next(n=no_atoms))
        elif not hasattr(param, '__iter__'):
            return numpy.array([param], dtype=float)
        elif len(param) != no_atoms:
            raise exceptions.ConfigurationException("The number of params does"
                                                    " not equal with the number "
                                                    "of atoms in the vertex ")
        else:
            return numpy.array(param, dtype=float)
