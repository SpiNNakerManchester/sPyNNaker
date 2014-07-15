from pacman.model.graph.vertex import Vertex
import logging
import numpy
import struct
#from spinnman.interfaces.transceiver_tools import scamp_constants
from spynnaker.pyNN import exceptions
from spynnaker.pyNN import conf
from spynnaker.pyNN.utilities.utility_calls \
    import get_app_data_base_address_offset, get_region_base_address_offset
from spynnaker.pyNN.utilities import constants
logger = logging.getLogger(__name__)

RECORDING_BASE_BYTES = 4


class ComponentVertex(Vertex):
    """
    Underlying Vertex model for Neural Applications.
    """
    
    def __init__(self, n_neurons, constraints=None, label=None):
        Vertex.__init__(self, n_neurons, constraints=constraints, label=label)
        
        self._record = False
        self.focus_level = None
        self._app_mask = constants.DEFAULT_MASK
        
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
    
    def record(self, focus=None):
        """
        method that sets the vertex to be recordable, as well as data on how the
        visuliser is to represent this vertex at runtime if at all
        """
        self._record = True
        # set the focus level and stuff for the vis
        self.focus_level = focus  # None, False, True

    @staticmethod
    def get_recording_region_size(no_machine_time_steps, bytes_per_timestep):
        """
        Gets the size of a recording region in bytes
        """
        if no_machine_time_steps is None:
            raise Exception("This model cannot record this parameter"
                            + " without a fixed run time")
        return RECORDING_BASE_BYTES + (no_machine_time_steps *
                                       bytes_per_timestep)

    def get_commands(self, no_tics):
        """
        method for any mc packets that need to be sent by the multicast_source
        """
        raise NotImplementedError

    def requires_multi_cast_source(self):
        """
        requires a multi_cast source
        """
        raise NotImplementedError

    def generate_routing_info(self, subedge):
        """
        For the given subedge generate the key and mask for routing.

        :param subedge: The subedge for which to generate the key and mask.
        :returns: A tuple containing the key and mask.
        """
        x, y, p = subedge.presubvertex.placement.processor.get_coordinates()

        key = packet_conversions.get_key_from_coords(x, y, p)
        #bodge to deal with external perrifables
        return key, self._app_mask

    def get_dependant_vertexes_edges(self):
        """
        method that allows models to add dependant vertexes and edges
        """
        raise NotImplementedError

    @property
    def is_set_to_record_spikes(self):
        """
        method to return if the vertex is set to be recorded
        """
        return self._record

    def _get_spikes(self, controller, compatible_output, spike_recording_region,
                    sub_vertex_out_spike_bytes_function, runtime, sub_graph,
                    placements):
        """
        Return a 2-column numpy array containing cell ids and spike times for 
        recorded cells.   This is read directly from the memory for the board.
        """
        
        logger.info("Getting spikes for {%s}".format(self.label))
        
        spikes = numpy.zeros((0, 2))
        
        # Find all the sub-vertices that this population.py exists on
        subvertices = sub_graph.get_subvertices_from_vertex(self)
        for subvertex in subvertices:
            placement = placements.get_subvertex_placement(subvertex)
            (x, y, p) = placement.processor.get_coordinates()
            logger.debug("Reading spikes from chip {%d}, {%d}, core {%d}, "
                         "lo_atom {%d}".format(x, y, p, subvertex.lo_atom))
            
            # Get the App Data for the core
            app_data_base_address_offset = get_app_data_base_address_offset(p)
            app_data_base_address_buf = \
                controller.txrx.read_mem(x, y, app_data_base_address_offset, 4)
            app_data_base_address = \
                struct.unpack("<I", app_data_base_address_buf)[0]
            
            # Get the position of the spike buffer
            spike_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address,
                                               spike_recording_region)
            spike_region_base_address_buf = \
                controller.txrx.read_mem(x, y, spike_region_base_address_offset,
                                         4)
            spike_region_base_address = \
                struct.unpack("<I", spike_region_base_address_buf)[0]
            spike_region_base_address += app_data_base_address
            
            # Read the spike data size
            number_of_bytes_written_buf =\
                controller.txrx.memory_calls.read_mem(x, y,
                                                      spike_region_base_address,
                                                      4)
            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]

            #check that the number of spikes written is smaller or the same as
            #  the size of the memory region we allocated for spikes
            out_spike_bytes = sub_vertex_out_spike_bytes_function(subvertex)
            machine_time_step = conf.config.getint("Machine", "machineTimeStep")
            no_machine_time_steps = int((runtime * 1000.0) / machine_time_step)
            size_of_region = \
                self.get_recording_region_size(out_spike_bytes,
                                               no_machine_time_steps)

            if number_of_bytes_written > size_of_region:
                raise exceptions.MemReadException("the amount of memory written"
                                                  " was larger than was "
                                                  "allocated for it")
            
            # Read the spikes
            logger.debug("Reading {%d} ({%s}) bytes starting at {%s} + 4"
                         .format(number_of_bytes_written,
                                 hex(number_of_bytes_written),
                                 hex(spike_region_base_address)))
            spike_data =\
                controller.txrx.memory_calls.read_mem(
                    x, y, spike_region_base_address + 4,
                    number_of_bytes_written)
            
            # Extract number of spike bytes from subvertex
            out_spike_bytes = sub_vertex_out_spike_bytes_function(subvertex)
            number_of_time_steps_written = \
                number_of_bytes_written / out_spike_bytes
            
            logger.debug("Processing {%d} timesteps"
                         .format(number_of_time_steps_written))
            
            # Loop through ticks
            for tick in range(0, number_of_time_steps_written):
                
                # Convert tick to ms
                time = tick * (controller.dao.machineTimeStep / 1000.0)
                
                # Get offset into file data that the bit vector representing 
                # the state at this tick begins at
                vector_offset = (tick * out_spike_bytes)
                
                # Loop through the words that make up this vector
                for neuronWordIndex in range(0, out_spike_bytes, 4):
                    
                    # Unpack the word containing the spikingness of 32 neurons
                    spike_vector_word = \
                        struct.unpack_from("<I", spike_data,
                                           vector_offset + neuronWordIndex)
                    
                    if spike_vector_word != 0:
                        # Loop through each bit in this word
                        for neuronBitIndex in range(0, 32):
                            
                            # If the bit is set
                            neuron_bit_mask = (1 << neuronBitIndex)
                            if (spike_vector_word[0] & neuron_bit_mask) != 0:
                                
                                # Calculate neuron ID
                                neuron_id = ((neuronWordIndex * 8) +
                                             neuronBitIndex + subvertex.lo_atom)
                                
                                # Add spike time and neuron ID to returned lists
                                spikes = numpy.append(spikes,
                                                      [[time, neuron_id]], 0)
            
        if len(spikes) > 0:
            
            logger.debug("Arranging spikes as per output spec")
            
            if compatible_output:
                
                # Change the order to be neuronID : time (don't know why - this
                # is how it was done in the old code, so I am doing it here too)
                spikes[:, [0, 1]] = spikes[:, [1, 0]]
                
                # Sort by neuron ID and not by time 
                spike_index = numpy.lexsort((spikes[:, 1], spikes[:, 0]))
                spikes = spikes[spike_index]
                return spikes
            
            # If compatible output, return sorted by spike time
            spike_index = numpy.lexsort((spikes[:, 1], spikes[:, 0]))
            spikes = spikes[spike_index]
            return spikes
        
        print("No spikes recorded")
        return None