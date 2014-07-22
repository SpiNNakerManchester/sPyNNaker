from abc import ABCMeta
import struct
import logging

from six import add_metaclass
import numpy

from pacman.model.constraints.partitioner_maximum_size_constraint import \
    PartitionerMaximumSizeConstraint
from spynnaker.pyNN.models.abstract_models.abstract_component_vertex import \
    AbstractComponentVertex
from spynnaker.pyNN.models.neural_properties.abstract_population_manager \
    import PopulationManager
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.utility_calls import \
    get_region_base_address_offset
from spynnaker.pyNN.utilities import constants

logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(AbstractComponentVertex, PopulationManager):
    """
    Underlying Vertex model for Neural Populations.
    """
    
    def __init__(self, n_neurons, n_params, binary, label, max_atoms_per_core,
                 constraints=None):

        AbstractComponentVertex.__init__(self, label)
        PopulationManager.__init__(self, False, binary, n_neurons, label,
                                   constraints)
        #add the max atom per core constraint
        max_atom_per_core_constraint = \
            PartitionerMaximumSizeConstraint(max_atoms_per_core)
        self.add_constraint(max_atom_per_core_constraint)
        self._delay_vertex = None
        self._n_params = n_params

    def get_partition_dependent_vertices(self):
        if self._delay_vertex is not None:
            vals = list()
            vals.append(self._delay_vertex)
            return vals
        return None

    @property
    def delay_vertex(self):
        return self._delay_vertex

    @delay_vertex.setter
    def delay_vertex(self, delay_vertex):
        self._delay_vertex = delay_vertex
    
    def get_spikes(self, spinnaker, runtime, compatible_output=False):
        if not spinnaker.has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran,therefore spikes cannot be "
                "retrieved")

        # Spike sources store spike vectors optimally
        # so calculate min words to represent
        sub_vertex_out_spike_bytes_function = \
            lambda subvertex: constants.OUT_SPIKE_BYTES
        
        # Use standard behaviour to read spikes
        return self._getSpikes(spinnaker, compatible_output,
                               constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY,
                               sub_vertex_out_spike_bytes_function, runtime)
    
    def get_neuron_parameter(self, region, compatible_output, spinnaker,
                             machine_time_step):
        if not spinnaker.has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore gsyn cannot be "
                "retrieved")
        value = numpy.zeros((0, 3))
        
        # Find all the sub-vertices that this pynn_population.py exists on
        for subvertex in self.subvertices:
            (x, y, p) = subvertex.placement.processor.get_coordinates()
            
            # Get the App Data for the core
            app_data_base_address = \
                spinnaker.txrx.get_cpu_information_from_core(x, y, p).user[0]
            
            # Get the position of the value buffer
            v_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address, region)
            v_region_base_address_buf = \
                spinnaker.txrx.read_memory(x, y, v_region_base_address_offset,
                                           4)
            v_region_base_address = \
                struct.unpack("<I", v_region_base_address_buf)[0]
            v_region_base_address += app_data_base_address
            
            # Read the size
            number_of_bytes_written_buf = \
                spinnaker.txrx.read_memory(x, y, v_region_base_address, 4)
            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]
                    
            # Read the values
            logger.debug("Reading {%d} ({%s}) bytes starting at {%s}".format( 
                number_of_bytes_written, hex(number_of_bytes_written), 
                hex(v_region_base_address + 4)))
            v_data = spinnaker.txrx.read_memory(x, y, v_region_base_address + 4, 
                                                number_of_bytes_written)
            bytes_per_time_step = subvertex.n_atoms * 4
            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step
            ms_per_timestep = machine_time_step / 1000.0
            
            logger.debug("Processing {%d} timesteps"
                         .format(number_of_time_steps_written))
            
            # Standard fixed-point 'accum' type scaling
            size = len(v_data) / 4
            scale = numpy.zeros(size, dtype=numpy.float)
            scale.fill(float(0x7FFF))
            
            # Add an array for time and neuron id
            time = numpy.array([int(i / subvertex.n_atoms) * ms_per_timestep 
                                for i in range(size)], dtype=numpy.float)
            neuron_id = numpy.array([int(i % subvertex.n_atoms) + 
                                     subvertex.lo_atom for i in range(size)], 
                                    dtype=numpy.uint32)
            
            # Get the values

            # noinspection PyNoneFunctionAssignment
            temp_value = numpy.frombuffer(v_data, dtype="<i4")
            # noinspection PyTypeChecker
            temp_value = numpy.divide(temp_value, scale)
            temp_array = numpy.dstack((time, neuron_id, temp_value))
            temp_array = numpy.reshape(temp_array, newshape=(-1, 3))
            
            value = numpy.append(value, temp_array, axis=0)
        
        logger.debug("Arranging parameter output")
        
        if compatible_output:
            
            # Change the order to be neuronID : time (don't know why - this
            # is how it was done in the old code, so I am doing it here too)
            value[:, [0, 1, 2]] = value[:, [1, 0, 2]]
            
            # Sort by neuron ID and not by time 
            v_index = numpy.lexsort((value[:, 2], value[:, 1], value[:, 0]))
            value = value[v_index]
            return value
        
        # If not compatible output, we will sort by time (as NEST seems to do)
        v_index = numpy.lexsort((value[:, 2], value[:, 1], value[:, 0]))
        value = value[v_index]
        return value
    
    def get_v(self, spinnaker, machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for 
        recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        logger.info("Getting v for {%s}".format(self.label))
        if not spinnaker.has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore v cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY,
            compatible_output, spinnaker, machine_time_step)

    def get_gsyn(self, spinnaker, machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic
        conductances for recorded cells.

        :param spinnaker:
        :param compatible_output:
        """
        logger.info("Getting gsyn for {%s}".format(self.label))
        if not spinnaker.has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore gsyn cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            constants.POPULATION_BASED_REGIONS.GSYN_HISTORY, compatible_output,
            spinnaker, machine_time_step)

    def get_synaptic_data(self, spinnaker, presubvertex, pre_n_atoms,
                          postsubvertex, synapse_io):
        """
        helper method to add other data for get weights via syanptic manager
        """
        return self._get_synaptic_data(
            spinnaker, presubvertex, pre_n_atoms, postsubvertex,
            constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE, synapse_io,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX)
