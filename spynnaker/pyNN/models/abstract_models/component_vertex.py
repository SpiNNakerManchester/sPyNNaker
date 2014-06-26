from pacman103.lib import graph
import logging
import numpy
import struct
from pacman103.core.spinnman.scp import scamp
from pacman103.core.utilities import packet_conversions
from pacman103.core import exceptions
from pacman103 import conf
from pacman103.core.utilities.memory_utils import getAppDataBaseAddressOffset,\
                                        getRegionBaseAddressOffset
logger = logging.getLogger(__name__)

RECORDING_BASE_BYTES = 4

class ComponentVertex(graph.Vertex):
    """
    Underlying Vertex model for Neural Applications.
    """
    
    def __init__(self, n_neurons, constraints=None, label=None,
                 virtual=False):
        super(ComponentVertex, self).__init__(
                                              atoms=n_neurons,
                                              constraints=constraints,
                                              label=label,
                                              virtual=virtual)
        
        self._record = False
        self.focus_level = None
        self.visualiser_mode = None
        #topological views
        self.visualiser_2d_dimensions = None
        self.visualiser_no_colours = None
        self.visualiser_average_period_tics = None
        self.visualiser_longer_period_tics = None
        self.visualiser_update_screen_in_tics = None
        self.visualiser_reset_counters = None
        self.visualiser_reset_counter_period = None

        #raster views
        self.visualiser_raster_seperate = None
        self._app_mask = packet_conversions.get_default_mask()
        
        # Store a delay vertex here if required
        self._delay_vertex = None
        
    @property
    def delay_vertex(self):
        return self._delay_vertex
    
    @delay_vertex.setter
    def delay_vertex(self, delay_vertex):
        self._delay_vertex = delay_vertex
        
    def get_partition_dependent_vertices(self):
        if self._delay_vertex is not None:
            vals = list()
            vals.append(self._delay_vertex)
            return vals
        return None
    
    def record(self, focus=None, visualiser_mode=None,
               visualiser_2d_dimension=None,
               visualiser_raster_seperate=None,
               visualiser_no_colours=None,
               visualiser_average_period_tics=None,
               visualiser_longer_period_tics=None,
               visualiser_update_screen_in_tics=None,
               visualiser_reset_counters=None,
               visualiser_reset_counter_period=None):
        '''
        method that sets the vertex to be recordable, as well as data on how the
        visuliser is to represent this vertex at runtime if at all
        '''
        self._record = True
        # set the focus level and stuff for the vis
        self.focus_level = focus # None, False, True
        self.visualiser_mode = visualiser_mode # Raster, Topological
        self.visualiser_2d_dimensions = visualiser_2d_dimension # tuple with x and y dimsion if the mode is topological {'x':x, 'y':y}
        self.visualiser_raster_seperate = visualiser_raster_seperate # true or false
        self.visualiser_average_period_tics= visualiser_average_period_tics #value in timer tics
        if visualiser_no_colours is not None:
            self.visualiser_no_colours = visualiser_no_colours # count in an itnerger (also controls number of legend labels)
        else:
            self.visualiser_no_colours = 5
        self.visualiser_longer_period_tics = visualiser_longer_period_tics # other thing for tics
        self.visualiser_update_screen_in_tics = visualiser_update_screen_in_tics # how often the listener has to update the topolgical views
        self.visualiser_reset_counters = visualiser_reset_counters # true or false
        self.visualiser_reset_counter_period = visualiser_reset_counter_period # how often to reset the counters
    
    def get_recording_region_size(self, no_machine_time_steps, bytes_per_timestep):
        """
        Gets the size of a recording region in bytes
        """
        if no_machine_time_steps is None:
            raise Exception("This model cannot record this parameter"
                    + " without a fixed run time")
        return RECORDING_BASE_BYTES + (no_machine_time_steps * bytes_per_timestep)

    '''
    method for any mc packets that need to be sent by the multicast_source
    '''
    def get_commands(self, no_tics):
        return list()

    '''
    requires a multi_cast source
    '''
    def requires_multi_cast_source(self):
        return False

    '''
    allows users to modify their key and mask if needed
    '''
    def generate_routing_info( self, subedge ):
        """
        For the given subedge generate the key and mask for routing.

        :param subedge: The subedge for which to generate the key and mask.
        :returns: A tuple containing the key and mask.
        """
        x, y, p = subedge.presubvertex.placement.processor.get_coordinates()

        key = packet_conversions.get_key_from_coords(x, y, p)
        #bodge to deal with external perrifables
        return key, self._app_mask

    '''
    method that allows models to add dependant vertexes and edges
    '''
    def get_dependant_vertexes_edges(self):
        return None, None

    '''
    method to return if the vertex is set to be recorded
    '''
    @property
    def is_set_to_record_spikes(self):
        return self._record

    
    def _getSpikes(self, controller, compatible_output,
                   spikeRecordingRegion, subVertexOutSpikeBytesFunction,
                   runtime):
        """
        Return a 2-column numpy array containing cell ids and spike times for 
        recorded cells.   This is read directly from the memory for the board.
        """
        
        logger.info("Getting spikes for %s" % (self.label))
        
        spikes = numpy.zeros((0, 2))
        
        # Find all the sub-vertices that this population.py exists on
        for subvertex in self.subvertices:
            (x, y, p) = subvertex.placement.processor.get_coordinates()
            logger.debug("Reading spikes from chip %d, %d, core %d, lo_atom %d"
                     % (x, y, p, subvertex.lo_atom))
            controller.txrx.select(x, y)
            
            # Get the App Data for the core
            appDataBaseAddressOffset = getAppDataBaseAddressOffset(p)
            appDataBaseAddressBuf = controller.txrx.memory_calls.read_mem(
                    appDataBaseAddressOffset, scamp.TYPE_WORD, 4)
            appDataBaseAddress = struct.unpack("<I", appDataBaseAddressBuf)[0]
            
            # Get the position of the spike buffer
            spikeRegionBaseAddressOffset = getRegionBaseAddressOffset(
                    appDataBaseAddress, spikeRecordingRegion)
            spikeRegionBaseAddressBuf = controller.txrx.memory_calls.read_mem(
                    spikeRegionBaseAddressOffset, scamp.TYPE_WORD, 4)
            spikeRegionBaseAddress = struct.unpack("<I", 
                    spikeRegionBaseAddressBuf)[0]
            spikeRegionBaseAddress += appDataBaseAddress
            
            # Read the spike data size
            numberOfBytesWrittenBuf = controller.txrx.memory_calls.read_mem(
                    spikeRegionBaseAddress, scamp.TYPE_WORD, 4)
            numberOfBytesWritten = struct.unpack_from("<I", 
                    numberOfBytesWrittenBuf)[0]

            #check that the number of spikes written is smaller or the same as the size of the memory
            #region we allocated for spikes
            outSpikeBytes = subVertexOutSpikeBytesFunction(subvertex)
            machine_time_step = conf.config.getint("Machine", "machineTimeStep")
            no_machine_time_steps = int((runtime * 1000.0) / machine_time_step)
            size_of_region = self.get_recording_region_size(outSpikeBytes, no_machine_time_steps)

            if numberOfBytesWritten > size_of_region:
                raise exceptions.MemReadException("the amount of memory written was "
                                                  "larger than was allocated for it")

            
            # Read the spikes
            logger.debug("Reading %d (%s) bytes starting at %s + 4" %
                    (numberOfBytesWritten, hex(numberOfBytesWritten), 
                            hex(spikeRegionBaseAddress)))
            spikeData = controller.txrx.memory_calls.read_mem(
                    spikeRegionBaseAddress + 4, scamp.TYPE_WORD, 
                    numberOfBytesWritten)
            
            # Extract number of spike bytes from subvertex
            outSpikeBytes = subVertexOutSpikeBytesFunction(subvertex)
            numberOfTimeStepsWritten = numberOfBytesWritten / (outSpikeBytes)
            
            logger.debug("Processing %d timesteps" % numberOfTimeStepsWritten)
            
            # Loop through ticks
            for tick in range(0, numberOfTimeStepsWritten):
                
                # Convert tick to ms
                time = tick * (controller.dao.machineTimeStep / 1000.0)
                
                # Get offset into file data that the bit vector representing 
                # the state at this tick begins at
                vectorOffset = (tick * outSpikeBytes)
                
                # Loop through the words that make up this vector
                for neuronWordIndex in range(0, outSpikeBytes, 4):
                    
                    # Unpack the word containing the spikingness of 32 neurons
                    spikeVectorWord = struct.unpack_from("<I", spikeData,
                                             vectorOffset + neuronWordIndex)
                    
                    if spikeVectorWord != 0:
                        # Loop through each bit in this word
                        for neuronBitIndex in range(0, 32):
                            
                            # If the bit is set
                            neuronBitMask = (1 << neuronBitIndex)
                            if (spikeVectorWord[0] & neuronBitMask) != 0:
                                
                                # Calculate neuron ID
                                neuronID = ((neuronWordIndex * 8) + neuronBitIndex
                                        + subvertex.lo_atom)
                                
                                # Add spike time and neuron ID to returned lists
                                spikes = numpy.append(spikes, [[time, neuronID]], 0)
            
        if len(spikes) > 0:
            
            logger.debug("Arranging spikes as per output spec")
            
            if compatible_output == True:
                
                # Change the order to be neuronID : time (don't know why - this
                # is how it was done in the old code, so I am doing it here too)
                spikes[:,[0,1]] = spikes[:,[1,0]]
                
                # Sort by neuron ID and not by time 
                spikeIndex = numpy.lexsort((spikes[:,1],spikes[:,0]))
                spikes = spikes[spikeIndex]
                return spikes;
            
            # If compatible output, return sorted by spike time
            spikeIndex = numpy.lexsort((spikes[:,1], spikes[:,0]))
            spikes = spikes[spikeIndex]
            return spikes
        
        print("No spikes recorded")
        return None

