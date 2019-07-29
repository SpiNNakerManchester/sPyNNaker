# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import math
import numpy
import scipy.stats
from spinn_utilities.overrides import overrides
from data_specification.enums import DataType
from pacman.executor.injection_decorator import inject_items
from pacman.model.graphs.application import ApplicationVertex
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractGeneratesDataSpecification,
    AbstractHasAssociatedBinary, AbstractRewritesDataSpecification)
from spinn_front_end_common.interface.simulation import simulation_utilities
from spinn_front_end_common.utilities import (
    helpful_functions, globals_variables)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, SIMULATION_N_BYTES)
from spinn_front_end_common.utilities.utility_objs import ExecutableType
from spynnaker.pyNN.models.common import SimplePopulationSettable
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.abstract_models import (
    AbstractReadParametersBeforeSet)
from spynnaker.pyNN.models.neuron.implementations import Struct
from .poisson_source_machine_vertex import (
    PoissonSourceMachineVertex)

logger = logging.getLogger(__name__)

# uint32_t random_backoff_us; uint32_t time_between_spikes;
# UFRACT seconds_per_tick; REAL ticks_per_second;
# REAL slow_rate_per_tick_cutoff; REAL fast_rate_per_tick_cutoff;
# uint32_t first_source_id; uint32_t n_spike_sources;
# mars_kiss64_seed_t (uint[4]) spike_source_seed;
PARAMS_BASE_WORDS = 12

# start_scaled, end_scaled, is_fast_source, exp_minus_lambda, sqrt_lambda,
# isi_val, time_to_source, poisson_weight
PARAMS_WORDS_PER_NEURON = 8

START_OF_POISSON_GENERATOR_PARAMETERS = PARAMS_BASE_WORDS * 4
MICROSECONDS_PER_SECOND = 1000000.0
MICROSECONDS_PER_MILLISECOND = 1000.0
SLOW_RATE_PER_TICK_CUTOFF = 0.01  # as suggested by MH (between Exp and Knuth)
FAST_RATE_PER_TICK_CUTOFF = 10  # between Knuth algorithm and Gaussian approx.
_REGIONS = PoissonSourceMachineVertex.POISSON_SOURCE_REGIONS
OVERFLOW_TIMESTEPS_FOR_SDRAM = 5

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10


_PoissonSourceStruct = Struct([
    DataType.UINT32,  # Start Scaled
    DataType.UINT32,  # End Scaled
    DataType.UINT32,  # is_fast_source
    DataType.U032,    # exp^(-sources_per_tick)
    DataType.S1615,   # sqrt(sources_per_tick)
    DataType.UINT32,   # inter-source-interval
    DataType.UINT32,  # timesteps to next source
    DataType.S1615])  # weight value at this source


class PoissonSourceVertex(
        ApplicationVertex, AbstractGeneratesDataSpecification,
        AbstractHasAssociatedBinary,
        AbstractChangableAfterRun, AbstractReadParametersBeforeSet,
        AbstractRewritesDataSpecification, SimplePopulationSettable):
    """ A Poisson Spike source object
    """
    __slots__ = [
        "__change_requires_mapping",
        "__change_requires_neuron_parameters_reload",
        "__duration",
        "__machine_time_step",
        "__model",
        "__model_name",
        "__n_atoms",
        "__rate",
        "__poisson_weight",
        "__rng",
        "__seed",
        "__start",
        "__time_to_source",
        "__kiss_seed",
        "__n_subvertices",
        "__n_data_specs",
        "__max_rate",
        "__rate_change"]

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, constraints, label, rate, max_rate, start,
            duration, seed, max_atoms_per_core, model, poisson_weight):
        # pylint: disable=too-many-arguments
        super(PoissonSourceVertex, self).__init__(
            label, constraints, max_atoms_per_core)

        # atoms params
        self.__n_atoms = n_neurons
        self.__model_name = "PoissonSource"
        self.__model = model
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # check for changes parameters
        self.__change_requires_mapping = True
        self.__change_requires_neuron_parameters_reload = False

        # Store the parameters
        self.__max_rate = max_rate
        self.__rate = self.convert_rate(rate)
        self.__rate_change = numpy.zeros(self.__rate.size)
        self.__start = utility_calls.convert_param_to_numpy(start, n_neurons)
        self.__duration = utility_calls.convert_param_to_numpy(
            duration, n_neurons)
        self.__time_to_source = utility_calls.convert_param_to_numpy(
            0, n_neurons)
        self.__machine_time_step = None

        self.__poisson_weight = self.convert_weight(poisson_weight)

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self.__change_requires_neuron_parameters_reload = True

    @inject_items({
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        ApplicationVertex.get_resources_used_by_atoms,
        additional_arguments={"machine_time_step"}
    )
    def get_resources_used_by_atoms(self, vertex_slice, machine_time_step):
        # pylint: disable=arguments-differ

        poisson_params_sz = self.get_params_bytes(vertex_slice)
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            PoissonSourceMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz)

        # build resources as i currently know
        container = ResourceContainer(
            sdram=other,
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        return container

    @property
    def n_atoms(self):
        return self.__n_atoms

    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__n_subvertices += 1
        return PoissonSourceMachineVertex(
            resources_required, constraints, label)

    @property
    def rate(self):
        return self.__rate

    @property
    def poisson_weight(self):
        return self.__poisson_weight

    def convert_rate(self, rate):
        new_rates = utility_calls.convert_param_to_numpy(rate, self.__n_atoms)
        new_max = max(new_rates)
        if self.__max_rate is None:
            self.__max_rate = new_max
        return new_rates

    def convert_weight(self, poisson_weight):
        new_weights = utility_calls.convert_param_to_numpy(poisson_weight,
                                                           self.__n_atoms)
        return new_weights

    @rate.setter
    def rate(self, rate):
        new_rate = self.convert_rate(rate)
        self.__rate_change = new_rate - self.__rate
        self.__rate = new_rate

    @poisson_weight.setter
    def poisson_weight(self, poisson_weight):
        new_weight = self.convert_weight(poisson_weight)
        self.__poisson_weight = new_weight

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, start):
        self.__start = utility_calls.convert_param_to_numpy(
            start, self.__n_atoms)

    @property
    def duration(self):
        return self.__duration

    @duration.setter
    def duration(self, duration):
        self.__duration = utility_calls.convert_param_to_numpy(
            duration, self.__n_atoms)

    @property
    def seed(self):
        return self.__seed

    @seed.setter
    def seed(self, seed):
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None

    @staticmethod
    def get_params_bytes(vertex_slice):
        """ Gets the size of the poisson parameters in bytes
        :param vertex_slice:
        """
        return (PARAMS_BASE_WORDS +
                (vertex_slice.n_atoms * PARAMS_WORDS_PER_NEURON)) * 4

    def reserve_memory_regions(self, spec, placement, graph_mapper):
        """ Reserve memory regions for poisson source parameters and output\
            buffer.
        :param spec: the data specification writer
        :param placement: the location this vertex resides on in the machine
        :param graph_mapper: the mapping between app and machine graphs
        :return: None
        """
        spec.comment("\nReserving memory space for data regions:\n\n")

        # Reserve memory:
        spec.reserve_memory_region(
            region=_REGIONS.SYSTEM_REGION.value,
            size=SIMULATION_N_BYTES,
            label='setup')

        # reserve poisson params dsg region
        self._reserve_poisson_params_region(placement, graph_mapper, spec)

        placement.vertex.reserve_provenance_data_region(spec)

    def _reserve_poisson_params_region(self, placement, graph_mapper, spec):
        """ does the allocation for the poisson params region itself, as\
            it can be reused for setters after an initial run
        :param placement: the location on machine for this vertex
        :param graph_mapper: the mapping between machine and application graphs
        :param spec: the dsg writer
        :return:  None
        """
        spec.reserve_memory_region(
            region=_REGIONS.POISSON_PARAMS_REGION.value,
            size=self.get_params_bytes(graph_mapper.get_slice(
                placement.vertex)), label='PoissonParams')

    def _write_poisson_parameters(
            self, spec, graph, placement,
            vertex_slice, machine_time_step, time_scale_factor):
        """ Generate Neuron Parameter data for Poisson spike sources
        :param spec: the data specification writer
        :param vertex_slice:\
            the slice of atoms a machine vertex holds from its application\
            vertex
        :param machine_time_step: the time between timer tick updates.
        :param time_scale_factor:\
            the scaling between machine time step and real time
        :return: None
        """
        # pylint: disable=too-many-arguments, too-many-locals
        spec.comment("\nWriting Neuron Parameters for {} poisson sources:\n"
                     .format(vertex_slice.n_atoms))

        # Set the focus to the region
        spec.switch_write_focus(_REGIONS.POISSON_PARAMS_REGION.value)

        # Write the offset value
        max_offset = (
            machine_time_step * time_scale_factor) // _MAX_OFFSET_DENOMINATOR
        spec.write_value(
            int(math.ceil(max_offset / self.__n_subvertices)) *
            self.__n_data_specs)
        self.__n_data_specs += 1

        # Write the number of microseconds between sending spikes
        total_mean_rate = numpy.sum(self.__rate)
        if total_mean_rate > 0:
            max_spikes = numpy.sum(scipy.stats.poisson.ppf(
                1.0 - (1.0 / self.__rate), self.__rate))
            spikes_per_timestep = (
                max_spikes / (MICROSECONDS_PER_SECOND // machine_time_step))
            # avoid a possible division by zero / small number (which may
            # result in a value that doesn't fit in a uint32) by only
            # setting time_between_spikes if spikes_per_timestep is > 1
            time_between_spikes = 1.0
            if spikes_per_timestep > 1:
                time_between_spikes = (
                    (machine_time_step * time_scale_factor) /
                    (spikes_per_timestep * 2.0))
            spec.write_value(data=int(time_between_spikes))
        else:

            # If the rate is 0 or less, set a "time between spikes" of 1
            # to ensure that some time is put between spikes in event
            # of a rate change later on
            spec.write_value(data=1)

        # Write the number of seconds per timestep (unsigned long fract)
        spec.write_value(
            data=float(machine_time_step) / MICROSECONDS_PER_SECOND,
            data_type=DataType.U032)

        # Write the number of timesteps per second (integer)
        spec.write_value(
            data=int(MICROSECONDS_PER_SECOND / float(machine_time_step)))

        # Write the slow-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=SLOW_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the fast-rate-per-tick-cutoff (accum)
        spec.write_value(
            data=FAST_RATE_PER_TICK_CUTOFF, data_type=DataType.S1615)

        # Write the lo_atom id
        spec.write_value(data=vertex_slice.lo_atom)

        # Write the number of sources
        spec.write_value(data=vertex_slice.n_atoms)

        # Write the random seed (4 words), generated randomly!
        kiss_key = (vertex_slice.lo_atom, vertex_slice.hi_atom)
        if kiss_key not in self.__kiss_seed:
            if self.__rng is None:
                self.__rng = numpy.random.RandomState(self.__seed)
            self.__kiss_seed[kiss_key] = [
                self.__rng.randint(-0x80000000, 0x7FFFFFFF) + 0x80000000
                for _ in range(4)]
        for value in self.__kiss_seed[kiss_key]:
            spec.write_value(data=value)

        # Compute the start times in machine time steps
        start = self.__start[vertex_slice.as_slice]
        start_scaled = self._convert_ms_to_n_timesteps(
            start, machine_time_step)

        # Compute the end times as start times + duration in machine time steps
        # (where duration is not None)
        duration = self.__duration[vertex_slice.as_slice]
        end_scaled = numpy.zeros(len(duration), dtype="uint32")
        none_positions = numpy.isnan(duration)
        positions = numpy.invert(none_positions)
        end_scaled[none_positions] = 0xFFFFFFFF
        end_scaled[positions] = self._convert_ms_to_n_timesteps(
            start[positions] + duration[positions], machine_time_step)

        # Get the rates for the atoms
        rates = self.__rate[vertex_slice.as_slice].astype("float")

        # Compute the spikes per tick for each atom
        sources_per_tick = (
            rates * (float(machine_time_step) / MICROSECONDS_PER_SECOND))

        # Determine which sources are fast and which are slow
        is_fast_source = sources_per_tick >= SLOW_RATE_PER_TICK_CUTOFF
        is_faster_source = sources_per_tick >= FAST_RATE_PER_TICK_CUTOFF

        # Compute the e^-(sources_per_tick) for fast sources to allow fast
        # computation of the Poisson distribution to get the number of spikes
        # per timestep
        exp_minus_lambda = numpy.zeros(len(sources_per_tick), dtype="float")
        exp_minus_lambda[is_fast_source] = numpy.exp(
            -1.0 * sources_per_tick[is_fast_source])

        # Compute sqrt(lambda) for "faster" sources to allow Gaussian
        # approximation of the Poisson distribution to get the number of
        # spikes per timestep
        sqrt_lambda = numpy.zeros(len(sources_per_tick), dtype="float")
        sqrt_lambda[is_faster_source] = numpy.sqrt(
            sources_per_tick[is_faster_source])

        # Compute the inter-spike-interval for slow sources to get the average
        # number of timesteps between spikes
        isi_val = numpy.zeros(len(sources_per_tick), dtype="uint32")
        elements = numpy.logical_not(is_fast_source) & (sources_per_tick > 0)
        isi_val[elements] = (1.0 / sources_per_tick[elements]).astype(int)

        # Get the time to spike value
        time_to_source = self.__time_to_source[
            vertex_slice.as_slice].astype(int)
        changed_rates = (
            self.__rate_change[vertex_slice.as_slice].astype("bool") &
            elements)
        time_to_source[changed_rates] = 0

        poisson_weight = self.__poisson_weight[vertex_slice.as_slice]

        # Merge the arrays as parameters per atom
        data = numpy.dstack((
            start_scaled.astype("uint32"),
            end_scaled.astype("uint32"),
            is_fast_source.astype("uint32"),
            (exp_minus_lambda * (2 ** 32)).astype("uint32"),
            (sqrt_lambda * (2 ** 15)).astype("uint32"),
            isi_val.astype("uint32"),
            time_to_source.astype("uint32"),
            (poisson_weight * (2 ** 15)).astype("uint32")
        ))[0]

        spec.write_array(data)

    @staticmethod
    def _convert_ms_to_n_timesteps(value, machine_time_step):
        return numpy.round(
            value * (MICROSECONDS_PER_MILLISECOND / float(machine_time_step)))

    @staticmethod
    def _convert_n_timesteps_to_ms(value, machine_time_step):
        return (
            value / (MICROSECONDS_PER_MILLISECOND / float(machine_time_step)))

    @staticmethod
    def get_dtcm_usage_for_atoms():
        return 0

    @staticmethod
    def get_cpu_usage_for_atoms():
        return 0

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "graph": "MemoryMachineGraph"})
    @overrides(
        AbstractRewritesDataSpecification.regenerate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "graph"})
    def regenerate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, graph):
        # pylint: disable=too-many-arguments, arguments-differ

        # reserve the neuron parameters data region
        self._reserve_poisson_params_region(placement, graph_mapper, spec)

        # allocate parameters
        self._write_poisson_parameters(
            spec=spec, graph=graph, placement=placement,
            vertex_slice=graph_mapper.get_slice(placement.vertex),
            machine_time_step=machine_time_step,
            time_scale_factor=time_scale_factor)

        # end spec
        spec.end_specification()

    @overrides(AbstractRewritesDataSpecification
               .requires_memory_regions_to_be_reloaded)
    def requires_memory_regions_to_be_reloaded(self):
        return self.__change_requires_neuron_parameters_reload

    @overrides(AbstractRewritesDataSpecification.mark_regions_reloaded)
    def mark_regions_reloaded(self):
        self.__change_requires_neuron_parameters_reload = False

    @overrides(AbstractReadParametersBeforeSet.read_parameters_from_machine)
    def read_parameters_from_machine(
            self, transceiver, placement, vertex_slice):

        # locate sdram address to where the neuron parameters are stored
        poisson_parameter_region_sdram_address = \
            helpful_functions.locate_memory_region_for_placement(
                placement, _REGIONS.POISSON_PARAMS_REGION.value, transceiver)

        # shift past the extra stuff before neuron parameters that we don't
        # need to read
        poisson_parameter_parameters_sdram_address = \
            poisson_parameter_region_sdram_address + \
            START_OF_POISSON_GENERATOR_PARAMETERS

        # get size of poisson params
        size_of_region = self.get_params_bytes(vertex_slice)
        size_of_region -= START_OF_POISSON_GENERATOR_PARAMETERS

        # get data from the machine
        byte_array = transceiver.read_memory(
            placement.x, placement.y,
            poisson_parameter_parameters_sdram_address, size_of_region)

        # Convert the data to parameter values
        (start, end, is_fast_source, exp_minus_lambda, sqrt_lambda, isi,
         time_to_next_spike, poisson_weight) = _PoissonSourceStruct.read_data(
             byte_array, 0, vertex_slice.n_atoms)

        # Convert start values as timesteps into milliseconds
        self.__start[vertex_slice.as_slice] = self._convert_n_timesteps_to_ms(
            start, self.__machine_time_step)

        # Convert end values as timesteps to durations in milliseconds
        self.__duration[vertex_slice.as_slice] = (
            self._convert_n_timesteps_to_ms(end, self.__machine_time_step) -
            self.__start[vertex_slice.as_slice])

        # Work out the spikes per tick depending on if the source is
        # slow (isi), fast (exp) or faster (sqrt)
        is_fast_source = is_fast_source == 1.0
        sources_per_tick = numpy.zeros(len(is_fast_source), dtype="float")
        sources_per_tick[is_fast_source] = numpy.log(
            exp_minus_lambda[is_fast_source]) * -1.0
        is_faster_source = sqrt_lambda > 0
        sources_per_tick[is_faster_source] = numpy.square(
            sqrt_lambda[is_faster_source])
        slow_elements = isi > 0
        sources_per_tick[slow_elements] = 1.0 / isi[slow_elements]

        # Convert spikes per tick to rates
        self.__rate[vertex_slice.as_slice] = (
            sources_per_tick *
            (MICROSECONDS_PER_SECOND / float(self.__machine_time_step)))

        # Store the updated time until next spike so that it can be
        # rewritten when the parameters are loaded
        self.__time_to_source[vertex_slice.as_slice] = time_to_next_spike

        self.__poisson_weight[vertex_slice.as_slice] = poisson_weight

    @inject_items({
        "machine_time_step": "MachineTimeStep",
        "time_scale_factor": "TimeScaleFactor",
        "graph_mapper": "MemoryGraphMapper",
        "routing_info": "MemoryRoutingInfos",
        "data_n_time_steps": "DataNTimeSteps",
        "graph": "MemoryMachineGraph"
    })
    @overrides(
        AbstractGeneratesDataSpecification.generate_data_specification,
        additional_arguments={
            "machine_time_step", "time_scale_factor", "graph_mapper",
            "routing_info", "data_n_time_steps", "graph"
        }
    )
    def generate_data_specification(
            self, spec, placement, machine_time_step, time_scale_factor,
            graph_mapper, routing_info, data_n_time_steps, graph):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__machine_time_step = machine_time_step
        vertex = placement.vertex
        vertex_slice = graph_mapper.get_slice(vertex)

        spec.comment("\n*** Spec for PoissonSource Instance ***\n\n")

        # Reserve SDRAM space for memory areas:
        self.reserve_memory_regions(spec, placement, graph_mapper)

        # write setup data
        spec.switch_write_focus(_REGIONS.SYSTEM_REGION.value)
        spec.write_array(simulation_utilities.get_simulation_header_array(
            self.get_binary_file_name(), machine_time_step,
            time_scale_factor))

        # write parameters
        self._write_poisson_parameters(
            spec, graph, placement, vertex_slice,
            machine_time_step, time_scale_factor)

        # End-of-Spec:
        spec.end_specification()

    @overrides(AbstractHasAssociatedBinary.get_binary_file_name)
    def get_binary_file_name(self):
        return "poisson_source.aplx"

    @overrides(AbstractHasAssociatedBinary.get_binary_start_type)
    def get_binary_start_type(self):
        return ExecutableType.USES_SIMULATION_INTERFACE

    def describe(self):
        """
        Returns a human-readable description of the cell or synapse type.
        The output may be customised by specifying a different template
        together with an associated template engine
        (see ``pyNN.descriptions``).
        If template is None, then a dictionary containing the template context
        will be returned.
        """

        parameters = dict()
        for parameter_name in self.__model.default_parameters:
            parameters[parameter_name] = self.get_value(parameter_name)

        context = {
            "name": self.__model_name,
            "default_parameters": self.__model.default_parameters,
            "default_initial_values": self.__model.default_parameters,
            "parameters": parameters,
        }
        return context

    @property
    def max_rate(self):
        return self.__max_rate
