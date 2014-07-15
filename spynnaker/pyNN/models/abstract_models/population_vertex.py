from pacman.model.constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint

from spynnaker.pyNN.models.abstract_models.component_vertex import \
    ComponentVertex
from spynnaker.pyNN.models.abstract_models.partitionable_vertex \
    import PartitionableVertex
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.utility_calls import \
    get_app_data_base_address_offset, get_region_base_address_offset
from spynnaker.pyNN.models.neural_properties.synaptic_manager import \
    SynapticManager
from spynnaker.pyNN.utilities import packet_conversions
from spynnaker.pyNN.utilities import constants

from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

import numpy
import struct
import os
import math
import ctypes
import logging

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class PopulationVertex(ComponentVertex, SynapticManager, PartitionableVertex):
    """
    Underlying Vertex model for Neural Populations.
    """
    
    def __init__(self, n_neurons, n_params, binary, label, max_atoms_per_core,
                 constraints=None):

        ComponentVertex.__init__(self, label)
        SynapticManager.__init__(self)
        PartitionableVertex.__init__(self, n_neurons, label, constraints)
        #add the max atom per core constraint
        max_atom_per_core_constraint = \
            PartitionerMaximumSizeConstraint(max_atoms_per_core)
        self.add_constraint(max_atom_per_core_constraint)

        self._n_params = n_params
        self._binary = binary
        
        self._record_v = False
        self._record_gsyn = False
        
    def record_v(self):
        self._record_v = True
    
    def record_gsyn(self):
        self._record_gsyn = True
    
    def reserve_memory_regions(self, spec, setup_sz, neuron_params_sz,
                               synapse_params_sz, row_len_trans_sz,
                               master_pop_table_sz, all_syn_block_sz,
                               spike_hist_buff_sz, potential_hist_buff_sz,
                               gsyn_hist_buff_sz, stdp_params_sz):
        """
        Reserve SDRAM space for memory areas:
        1) Area for information on what data to record
        2) Neuron parameter data (will be copied to DTCM by 'C'
           code at start-up)
        3) synapse parameter data (will be copied to DTCM)
        4) Synaptic row length look-up (copied to DTCM)
        5) Synaptic block look-up table. Translates the start address
           of each block of synapses (copied to DTCM)
        6) Synaptic row data (lives in SDRAM)
        7) Spike history
        8) Neuron potential history
        9) Gsyn value history
        """

        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserveMemRegion(region=constants.REGIONS.SYSTEM,
                              size=setup_sz,
                              label='setup')
        spec.reserveMemRegion(region=constants.REGIONS.NEURON_PARAMS,
                              size=neuron_params_sz,
                              label='NeuronParams')
        spec.reserveMemRegion(region=constants.REGIONS.SYNAPSE_PARAMS,
                              size=synapse_params_sz,
                              label='SynapseParams')
        spec.reserveMemRegion(region=constants.REGIONS.ROW_LEN_TRANSLATION,
                              size=row_len_trans_sz,
                              label='RowLenTable')
        spec.reserveMemRegion(region=constants.REGIONS.MASTER_POP_TABLE,
                              size=master_pop_table_sz,
                              label='MasterPopTable')
        spec.reserveMemRegion(region=constants.REGIONS.SYNAPTIC_MATRIX,
                              size=all_syn_block_sz,
                              label='SynBlocks')

        if self._record:
            spec.reserveMemRegion(region=constants.REGIONS.SPIKE_HISTORY,
                                  size=spike_hist_buff_sz,
                                  label='spikeHistBuffer',
                                  leaveUnfilled=True)
        if self._record_v:
            spec.reserveMemRegion(region=constants.REGIONS.POTENTIAL_HISTORY,
                                  size=potential_hist_buff_sz,
                                  label='potHistBuffer',
                                  leaveUnfilled=True)
        if self._record_gsyn:
            spec.reserveMemRegion(region=constants.REGIONS.GSYN_HISTORY,
                                  size=gsyn_hist_buff_sz,
                                  label='gsynHistBuffer',
                                  leaveUnfilled=True)
        if stdp_params_sz != 0:
            spec.reserveMemRegion(region=constants.REGIONS.STDP_PARAMS,
                                  size=stdp_params_sz,
                                  label='stdpParams')

    def write_setup_info(self, spec, spike_history_region_sz,
                         neuron_potential_region_sz, gsyn_region_sz):
        """
        Write information used to control the simulation and gathering of
        results.Currently, this means the flag word used to signal whether
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
        # What recording commands were set for the parent population.py?
        recording_info = 0
        if spike_history_region_sz > 0 and self._record:
            recording_info |= constants.RECORD_SPIKE_BIT
        if neuron_potential_region_sz > 0 and self._record_v:
            recording_info |= constants.RECORD_STATE_BIT
        if gsyn_region_sz > 0 and self._record_gsyn:
            recording_info |= constants.RECORD_GSYN_BIT
        recording_info |= 0xBEEF0000

        # Write this to the system region (to be picked up by the simulation):
        spec.switchWriteFocus(region=constants.REGIONS.SYSTEM)
        spec.write(data=recording_info)
        spec.write(data=spike_history_region_sz)
        spec.write(data=neuron_potential_region_sz)
        spec.write(data=gsyn_region_sz)
        
    def write_neuron_parameters(self, spec, machine_time_step, processor,
                                subvertex, ring_buffer_to_input_left_shift):
        spec.comment("\nWriting Neuron Parameters for {%d} "
                     "Neurons:\n".format(subvertex.n_atoms))

        # Set the focus to the memory region 2 (neuron parameters):
        spec.switchWriteFocus(region=constants.REGIONS.NEURON_PARAMS)

        # Write header info to the memory region:
        # Write Key info for this core:
        chip_x, chip_y, chip_p = processor.get_coordinates()
        population_identity = \
            packet_conversions.get_key_from_coords(chip_x, chip_y, chip_p)
        spec.write(data=population_identity)

        # Write the number of neurons in the block:
        spec.write(data=subvertex.n_atoms)

        # Write the number of parameters per neuron (struct size in words):
        params = self.get_parameters(machine_time_step)
        spec.write(data=len(params))

        # Write machine time step: (Integer, expressed in microseconds)
        spec.write(data=machine_time_step)
        
        # Write ring_buffer_to_input_left_shift
        spec.write(data=ring_buffer_to_input_left_shift)
        
        # TODO: Took this out for now as I need random parameters
        # Create loop over number of neurons:
        #spec.loop(countReg = 15, startVal = 0, endVal = subvertex.n_atoms)
        for atom in range(0, subvertex.n_atoms):
            # Process the parameters
            for param in params:
                value = param.get_value()
                if hasattr(value, "__len__"):
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
    
    def get_parameters(self, machine_time_step):
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
        neuronParamsSz = self.get_neuron_params_size(subvertex.lo_atom,
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
        self.write_random_distribution_declarations(spec, dao)

        # Construct the data images needed for the Neuron:
        self.reserve_memory_regions(spec, SETUP_SIZE, neuronParamsSz,
                synapseParamsSz, SynapticManager.ROW_LEN_TABLE_SIZE,
                SynapticManager.MASTER_POPULATION_TABLE_SIZE, allSynBlockSz,
                spikeHistBuffSz, potentialHistBuffSz, gsynHistBuffSz,
                stdpRegionSz)

        self.write_setup_info(spec, subvertex, spikeHistBuffSz,
                potentialHistBuffSz, gsynHistBuffSz)

        ring_buffer_shift = self.get_ring_buffer_to_input_left_shift(subvertex)
        weight_scale = self.get_weight_scale(ring_buffer_shift)
        logger.debug("Weight scale is {}".format(weight_scale))
        
        self.write_neuron_parameters(spec, machineTimeStep, processor, subvertex,
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


