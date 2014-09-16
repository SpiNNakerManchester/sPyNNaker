from abc import ABCMeta
import struct
import logging

from six import add_metaclass
import numpy
from pacman.model.constraints.\
    partitioner_same_size_as_vertex_constraint import \
    PartitionerSameSizeAsVertexConstraint

from spynnaker.pyNN.models.abstract_models.abstract_recordable_vertex import \
    AbstractRecordableVertex
from spynnaker.pyNN.models.abstract_models.abstract_population_data_spec \
    import AbstractPopulationDataSpec
from spynnaker.pyNN import exceptions
from spynnaker.pyNN.utilities.utility_calls import \
    get_region_base_address_offset
from spynnaker.pyNN.utilities import constants


logger = logging.getLogger(__name__)


@add_metaclass(ABCMeta)
class AbstractPopulationVertex(AbstractRecordableVertex,
                               AbstractPopulationDataSpec):
    """
    Underlying AbstractConstrainedVertex model for Neural Populations.
    """
    
    def __init__(self, n_neurons, n_params, binary, label, max_atoms_per_core,
                 machine_time_step, constraints=None):

        AbstractRecordableVertex.__init__(self, machine_time_step, label)
        AbstractPopulationDataSpec.__init__(
            self, False, binary, n_neurons, label, constraints,
            machine_time_step=machine_time_step,
            max_atoms_per_core=max_atoms_per_core)
        self._delay_vertex = None
        self._n_params = n_params

    @property
    def delay_vertex(self):
        return self._delay_vertex

    @delay_vertex.setter
    def delay_vertex(self, delay_vertex):
        if self._delay_vertex is None:
            self._delay_vertex = delay_vertex
            self.add_constraint(
                PartitionerSameSizeAsVertexConstraint(self._delay_vertex))
        else:
            raise exceptions.ConfigurationException(
                "cannot set a vertex's delay vertex once its already been set")

    def get_spikes(self, has_ran, txrx, placements, graph_mapper,
                   compatible_output=False):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran,therefore spikes cannot be "
                "retrieved")

        # Spike sources store spike vectors optimally
        # so calculate min words to represent
        sub_vertex_out_spike_bytes_function = \
            lambda subvertex: constants.OUT_SPIKE_BYTES
        
        # Use standard behaviour to read spikes
        return self._get_spikes(
            graph_mapper=graph_mapper, placements=placements, transciever=txrx,
            compatible_output=compatible_output,
            sub_vertex_out_spike_bytes_function=
            sub_vertex_out_spike_bytes_function,
            spike_recording_region=
            constants.POPULATION_BASED_REGIONS.SPIKE_HISTORY.value)
    
    def get_neuron_parameter(
            self, region, compatible_output, has_ran, graph_mapper, placements, 
            txrx, machine_time_step):
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore gsyn cannot be "
                "retrieved")
        value = numpy.zeros((0, 3))
        
        # Find all the sub-vertices that this pynn_population.py exists on
        subvertices = graph_mapper.get_subvertices_from_vertex(self)
        for subvertex in subvertices:
            placment = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placment.x, placment.y, placment.p
            
            # Get the App Data for the core
            app_data_base_address = txrx.\
                get_cpu_information_from_core(x, y, p).user[0]
            
            # Get the position of the value buffer
            v_region_base_address_offset = \
                get_region_base_address_offset(app_data_base_address, region)
            v_region_base_address_buf = \
                str(list(txrx.
                         read_memory(x, y, v_region_base_address_offset, 4))[0])
            v_region_base_address = struct.unpack("<I",
                                                  v_region_base_address_buf)[0]
            v_region_base_address += app_data_base_address
            
            # Read the size
            number_of_bytes_written_buf = \
                str(list(txrx.
                         read_memory(x, y, v_region_base_address, 4))[0])
            number_of_bytes_written = \
                struct.unpack_from("<I", number_of_bytes_written_buf)[0]
                    
            # Read the values
            logger.debug("Reading {} ({}) bytes starting at {}".format(
                number_of_bytes_written, hex(number_of_bytes_written), 
                hex(v_region_base_address + 4)))
            v_data = \
                str(list(txrx.
                         read_memory(x, y, v_region_base_address + 4,
                                     number_of_bytes_written))[0])
            vertex_slice = graph_mapper.get_subvertex_slice(subvertex)
            n_atoms = (vertex_slice.hi_atom - vertex_slice.lo_atom) + 1
            bytes_per_time_step = n_atoms * 4
            number_of_time_steps_written = \
                number_of_bytes_written / bytes_per_time_step
            ms_per_timestep = machine_time_step / 1000.0
            
            logger.debug("Processing {} timesteps"
                         .format(number_of_time_steps_written))
            
            # Standard fixed-point 'accum' type scaling
            size = len(v_data) / 4
            scale = numpy.zeros(size, dtype=numpy.float)
            scale.fill(float(0x7FFF))
            
            # Add an array for time and neuron id
            time = numpy.array([int(i / n_atoms) * ms_per_timestep
                                for i in range(size)], dtype=numpy.float)
            lo_atom = vertex_slice.lo_atom
            neuron_id = numpy.array([int(i % n_atoms) +
                                     lo_atom for i in range(size)],
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
    
    def get_v(self, has_ran, graph_mapper, placements,
              txrx, machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids, time, and Vm for 
        recorded cells.

        :param bool gather:
            not used - inserted to match PyNN specs
        :param bool compatible_output:
            not used - inserted to match PyNN specs
        """
        logger.info("Getting v for {}".format(self.label))
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore v cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            region=constants.POPULATION_BASED_REGIONS.POTENTIAL_HISTORY.value,
            compatible_output=compatible_output, has_ran=has_ran,
            machine_time_step=machine_time_step, graph_mapper=graph_mapper,
            placements=placements, txrx=txrx)

    def get_gsyn(self, has_ran, graph_mapper, placements, txrx,
                 machine_time_step, compatible_output=False):
        """
        Return a 3-column numpy array containing cell ids and synaptic
        conductances for recorded cells.

        :param compatible_output:
        """
        logger.info("Getting gsyn for {}".format(self.label))
        if not has_ran:
            raise exceptions.SpynnakerException(
                "The simulation has not yet ran, therefore gsyn cannot be "
                "retrieved")
        return self.get_neuron_parameter(
            region=constants.POPULATION_BASED_REGIONS.GSYN_HISTORY.value,
            compatible_output=compatible_output, has_ran=has_ran,
            machine_time_step=machine_time_step, graph_mapper=graph_mapper,
            placements=placements, txrx=txrx)

    def get_synaptic_data(self, presubvertex, pre_n_atoms, postsubvertex,
                          synapse_io):
        """
        helper method to add other data for get weights via syanptic manager
        """
        return self._get_synaptic_data(
            presubvertex, pre_n_atoms, postsubvertex,
            constants.POPULATION_BASED_REGIONS.MASTER_POP_TABLE.value,
            synapse_io,
            constants.POPULATION_BASED_REGIONS.SYNAPTIC_MATRIX.value)
