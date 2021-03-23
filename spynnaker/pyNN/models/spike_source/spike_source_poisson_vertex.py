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
from spinn_utilities.log import FormatAdapter
from spinn_utilities.overrides import overrides
from pacman.model.partitioner_interfaces import LegacyPartitionerAPI
from pacman.executor.injection_decorator import inject_items
from pacman.model.constraints.key_allocator_constraints import (
    ContiguousKeyRangeContraint)
from pacman.model.resources import (
    ConstantSDRAM, CPUCyclesPerTickResource, DTCMResource, ResourceContainer)
from spinn_front_end_common.abstract_models import (
    AbstractChangableAfterRun, AbstractProvidesOutgoingPartitionConstraints,
    AbstractRewritesDataSpecification)
from spinn_front_end_common.abstract_models.impl import (
    ProvidesKeyToAtomMappingImpl, TDMAAwareApplicationVertex)
from spinn_front_end_common.interface.buffer_management import (
    recording_utilities)
from spinn_front_end_common.utilities import (
    helpful_functions, globals_variables)
from spinn_front_end_common.utilities.constants import (
    SYSTEM_BYTES_REQUIREMENT, MICRO_TO_SECOND_CONVERSION)
from spinn_front_end_common.interface.profiling import profile_utils
from spynnaker.pyNN.models.common import (
    AbstractSpikeRecordable, MultiSpikeRecorder, SimplePopulationSettable)
from .spike_source_poisson_machine_vertex import (
    SpikeSourcePoissonMachineVertex, _flatten, get_rates_bytes)
from spynnaker.pyNN.utilities.utility_calls import create_mars_kiss_seeds
from spynnaker.pyNN.utilities.ranged.spynnaker_ranged_dict \
    import SpynnakerRangeDictionary
from spynnaker.pyNN.utilities.ranged.spynnaker_ranged_list \
    import SpynnakerRangedList

logger = FormatAdapter(logging.getLogger(__name__))

# uint32_t n_rates; uint32_t index
PARAMS_WORDS_PER_NEURON = 2

# start_scaled, end_scaled, next_scaled, is_fast_source, exp_minus_lambda,
# sqrt_lambda, isi_val, time_to_spike
PARAMS_WORDS_PER_RATE = 8

SLOW_RATE_PER_TICK_CUTOFF = (
    SpikeSourcePoissonMachineVertex.SLOW_RATE_PER_TICK_CUTOFF)

OVERFLOW_TIMESTEPS_FOR_SDRAM = 5

# The microseconds per timestep will be divided by this to get the max offset
_MAX_OFFSET_DENOMINATOR = 10


class SpikeSourcePoissonVertex(
        TDMAAwareApplicationVertex, AbstractSpikeRecordable,
        AbstractProvidesOutgoingPartitionConstraints,
        AbstractChangableAfterRun, SimplePopulationSettable,
        ProvidesKeyToAtomMappingImpl, LegacyPartitionerAPI):
    """ A Poisson Spike source object
    """

    __slots__ = [
        "__change_requires_mapping",
        "__duration",
        "__model",
        "__model_name",
        "__n_atoms",
        "__rate",
        "__rng",
        "__seed",
        "__spike_recorder",
        "__start",
        "__time_to_spike",
        "__kiss_seed",  # dict indexed by vertex slice
        "__n_subvertices",
        "__n_data_specs",
        "__max_rate",
        "__rate_change",
        "__n_profile_samples",
        "__data",
        "__is_variable_rate",
        "__max_spikes"]

    SPIKE_RECORDING_REGION_ID = 0

    def __init__(
            self, n_neurons, constraints, label, seed,
            max_atoms_per_core, model, rate=None, start=None,
            duration=None, rates=None, starts=None, durations=None,
            max_rate=None, splitter=None):
        """
        :param int n_neurons:
        :param constraints:
        :type constraints:
            iterable(~pacman.model.constraints.AbstractConstraint)
        :param str label:
        :param float seed:
        :param int max_atoms_per_core:
        :param ~spynnaker.pyNN.models.spike_source.SpikeSourcePoisson model:
        :param iterable(float) rate:
        :param iterable(int) start:
        :param iterable(int) duration:
        :param splitter:
        :type splitter:
            ~pacman.model.partitioner_splitters.abstract_splitters.AbstractSplitterCommon
        """
        # pylint: disable=too-many-arguments
        super().__init__(label, constraints, max_atoms_per_core, splitter)

        # atoms params
        self.__n_atoms = self.round_n_atoms(n_neurons, "n_neurons")
        self.__model_name = "SpikeSourcePoisson"
        self.__model = model
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None
        self.__n_subvertices = 0
        self.__n_data_specs = 0

        # check for changes parameters
        self.__change_requires_mapping = True

        self.__spike_recorder = MultiSpikeRecorder()

        # Check for disallowed pairs of parameters
        if (rates is not None) and (rate is not None):
            raise Exception("Exactly one of rate and rates can be specified")
        if (starts is not None) and (start is not None):
            raise Exception("Exactly one of start and starts can be specified")
        if (durations is not None) and (duration is not None):
            raise Exception(
                "Exactly one of duration and durations can be specified")
        if rate is None and rates is None:
            raise Exception("One of rate or rates must be specified")

        # Normalise the parameters
        self.__is_variable_rate = rates is not None
        if rates is None:
            if hasattr(rate, "__len__"):
                # Single rate per neuron for whole simulation
                rates = [numpy.array([r]) for r in rate]
            else:
                # Single rate for all neurons for whole simulation
                rates = numpy.array([rate])
        elif hasattr(rates[0], "__len__"):
            # Convert each list to numpy array
            rates = [numpy.array(r) for r in rates]
        else:
            rates = numpy.array(rates)
        if starts is None and start is not None:
            if hasattr(start, "__len__"):
                starts = [numpy.array([s]) for s in start]
            elif start is None:
                starts = numpy.array([0])
            else:
                starts = numpy.array([start])
        elif starts is not None and hasattr(starts[0], "__len__"):
            starts = [numpy.array(s) for s in starts]
        elif starts is not None:
            starts = numpy.array(starts)
        if durations is None and duration is not None:
            if hasattr(duration, "__len__"):
                durations = [numpy.array([d]) for d in duration]
            else:
                durations = numpy.array([duration])
        elif durations is not None and hasattr(durations[0], "__len__"):
            durations = [numpy.array(d) for d in durations]
        elif durations is not None:
            durations = numpy.array(durations)
        else:
            if hasattr(rates[0], "__len__"):
                durations = [numpy.array([None for r in _rate])
                             for _rate in rates]
            else:
                durations = numpy.array([None for _rate in rates])

        # Check that there is either one list for all neurons,
        # or one per neuron
        if hasattr(rates[0], "__len__") and len(rates) != n_neurons:
            raise Exception(
                "Must specify one rate for all neurons or one per neuron")
        if (starts is not None and hasattr(starts[0], "__len__") and
                len(starts) != n_neurons):
            raise Exception(
                "Must specify one start for all neurons or one per neuron")
        if (durations is not None and hasattr(durations[0], "__len__") and
                len(durations) != n_neurons):
            raise Exception(
                "Must specify one duration for all neurons or one per neuron")

        # Check that for each rate there is a start and duration if needed
        # TODO: Could be more efficient for case where parameters are not one
        #       per neuron
        for i in range(n_neurons):
            rate_set = rates
            if hasattr(rates[0], "__len__"):
                rate_set = rates[i]
            if not hasattr(rate_set, "__len__"):
                raise Exception("Multiple rates must be a list")
            if starts is None and len(rate_set) > 1:
                raise Exception(
                    "When multiple rates are specified,"
                    " each must have a start")
            elif starts is not None:
                start_set = starts
                if hasattr(starts[0], "__len__"):
                    start_set = starts[i]
                if len(start_set) != len(rate_set):
                    raise Exception("Each rate must have a start")
                if any(s is None for s in start_set):
                    raise Exception("Start must not be None")
            if durations is not None:
                duration_set = durations
                if hasattr(durations[0], "__len__"):
                    duration_set = durations[i]
                if len(duration_set) != len(rate_set):
                    raise Exception("Each rate must have its own duration")

        if hasattr(rates[0], "__len__"):
            time_to_spike = [
                numpy.array([0 for _ in range(len(rates[i]))])
                for i in range(len(rates))]
        else:
            time_to_spike = numpy.array([0 for _ in range(len(rates))])

        self.__data = SpynnakerRangeDictionary(n_neurons)
        self.__data["rates"] = SpynnakerRangedList(
            n_neurons, rates,
            use_list_as_value=not hasattr(rates[0], "__len__"))
        self.__data["starts"] = SpynnakerRangedList(
            n_neurons, starts,
            use_list_as_value=not hasattr(starts[0], "__len__"))
        self.__data["durations"] = SpynnakerRangedList(
            n_neurons, durations,
            use_list_as_value=not hasattr(durations[0], "__len__"))
        self.__data["time_to_spike"] = SpynnakerRangedList(
            n_neurons, time_to_spike,
            use_list_as_value=not hasattr(time_to_spike[0], "__len__"))
        self.__rng = numpy.random.RandomState(seed)
        self.__rate_change = numpy.zeros(n_neurons)

        # get config from simulator
        config = globals_variables.get_simulator().config
        self.__n_profile_samples = helpful_functions.read_config_int(
            config, "Reports", "n_profile_samples")

        # Prepare for recording, and to get spikes
        self.__spike_recorder = MultiSpikeRecorder()

        all_rates = list(_flatten(self.__data["rates"]))
        self.__max_rate = max_rate
        if max_rate is None and len(all_rates):
            self.__max_rate = numpy.amax(all_rates)
        elif max_rate is None:
            self.__max_rate = 0

        total_rate = numpy.sum(all_rates)
        self.__max_spikes = 0
        if total_rate > 0:
            # Note we have to do this per rate, as the whole array is not numpy
            max_rates = numpy.array(
                [numpy.max(r) for r in self.__data["rates"]])
            self.__max_spikes = numpy.sum(scipy.stats.poisson.ppf(
                1.0 - (1.0 / max_rates), max_rates))

    @property
    def n_profile_samples(self):
        return self.__n_profile_samples

    @property
    def rate(self):
        if self.__is_variable_rate:
            raise Exception("Get variable rate poisson rates with .rates")
        return list(_flatten(self.__data["rates"]))

    @rate.setter
    def rate(self, rate):
        if self.__is_variable_rate:
            raise Exception("Cannot set rate of a variable rate poisson")
        self.__rate_change = rate - numpy.array(
            list(_flatten(self.__data["rates"])))
        # Normalise parameter
        if hasattr(rate, "__len__"):
            # Single rate per neuron for whole simulation
            self.__data["rates"].set_value([numpy.array([r]) for r in rate])
        else:
            # Single rate for all neurons for whole simulation
            self.__data["rates"].set_value(
                numpy.array([rate]), use_list_as_value=True)
        all_rates = list(_flatten(self.__data["rates"]))
        new_max = 0
        if len(all_rates):
            new_max = numpy.amax(all_rates)
        if self.__max_rate is None:
            self.__max_rate = new_max
        # Setting record forces reset so OK to go over if not recording
        elif self.__spike_recorder.record and new_max > self.__max_rate:
            logger.info('Increasing spike rate while recording requires a '
                        '"reset unless additional_parameters "max_rate" is '
                        'set')
            self.__change_requires_mapping = True
            self.__max_rate = new_max

    @property
    def start(self):
        return self.__data["starts"]

    @start.setter
    def start(self, start):
        if self.__is_variable_rate:
            raise Exception("Cannot set start of a variable rate poisson")
        # Normalise parameter
        if hasattr(start, "__len__"):
            # Single start per neuron for whole simulation
            self.__data["starts"].set_value([numpy.array([s]) for s in start])
        else:
            # Single start for all neurons for whole simulation
            self.__data["starts"].set_value(
                numpy.array([start]), use_list_as_value=True)

    @property
    def duration(self):
        return self.__data["durations"]

    @duration.setter
    def duration(self, duration):
        if self.__is_variable_rate:
            raise Exception("Cannot set duration of a variable rate poisson")
        # Normalise parameter
        if hasattr(duration, "__len__"):
            # Single duration per neuron for whole simulation
            self.__data["durations"].set_value(
                [numpy.array([d]) for d in duration])
        else:
            # Single duration for all neurons for whole simulation
            self.__data["durations"].set_value(
                numpy.array([duration]), use_list_as_value=True)

    @property
    def rates(self):
        return self.__data["rates"]

    @rates.setter
    def rates(self, _rates):
        if self.__is_variable_rate:
            raise Exception("Cannot set rates of a variable rate poisson")
        raise Exception("Set the rate of a Poisson source using rate")

    @property
    def starts(self):
        return self.__data["starts"]

    @starts.setter
    def starts(self, _starts):
        if self.__is_variable_rate:
            raise Exception("Cannot set starts of a variable rate poisson")
        raise Exception("Set the start of a Poisson source using start")

    @property
    def durations(self):
        return self.__data["durations"]

    @durations.setter
    def durations(self, _durations):
        if self.__is_variable_rate:
            raise Exception("Cannot set durations of a variable rate poisson")
        raise Exception("Set the duration of a Poisson source using duration")

    @property
    def time_to_spike(self):
        return self.__data["time_to_spike"]

    @property
    def rate_change(self):
        return self.__rate_change

    @property
    @overrides(AbstractChangableAfterRun.requires_mapping)
    def requires_mapping(self):
        return self.__change_requires_mapping

    @overrides(AbstractChangableAfterRun.mark_no_changes)
    def mark_no_changes(self):
        self.__change_requires_mapping = False

    @overrides(SimplePopulationSettable.set_value)
    def set_value(self, key, value):
        super().set_value(key, value)
        for machine_vertex in self.machine_vertices:
            if isinstance(machine_vertex, AbstractRewritesDataSpecification):
                machine_vertex.set_reload_required(True)

    def max_spikes_per_ts(self, machine_time_step):
        """
        :param int machine_time_step:
        """
        ts_per_second = MICRO_TO_SECOND_CONVERSION / float(machine_time_step)
        if float(self.__max_rate) / ts_per_second < \
                SLOW_RATE_PER_TICK_CUTOFF:
            return 1

        # Experiments show at 1000 this result is typically higher than actual
        chance_ts = 1000
        max_spikes_per_ts = scipy.stats.poisson.ppf(
            1.0 - (1.0 / float(chance_ts)),
            float(self.__max_rate) / ts_per_second)
        return int(math.ceil(max_spikes_per_ts)) + 1.0

    def get_recording_sdram_usage(self, vertex_slice, machine_time_step):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int machine_time_step:
        """
        variable_sdram = self.__spike_recorder.get_sdram_usage_in_bytes(
            vertex_slice.n_atoms, self.max_spikes_per_ts(machine_time_step))
        constant_sdram = ConstantSDRAM(
            variable_sdram.per_timestep * OVERFLOW_TIMESTEPS_FOR_SDRAM)
        return variable_sdram + constant_sdram

    @inject_items({
        "machine_time_step": "MachineTimeStep"
    })
    @overrides(
        LegacyPartitionerAPI.get_resources_used_by_atoms,
        additional_arguments={"machine_time_step"}
    )
    def get_resources_used_by_atoms(self, vertex_slice, machine_time_step):
        """
        :param ~pacman.model.graphs.common.Slice vertex_slice:
        :param int machine_time_step:
        """
        # pylint: disable=arguments-differ
        poisson_params_sz = get_rates_bytes(vertex_slice, self.__data["rates"])
        other = ConstantSDRAM(
            SYSTEM_BYTES_REQUIREMENT +
            SpikeSourcePoissonMachineVertex.get_provenance_data_size(0) +
            poisson_params_sz + self.tdma_sdram_size_in_bytes +
            recording_utilities.get_recording_header_size(1) +
            recording_utilities.get_recording_data_constant_size(1) +
            profile_utils.get_profile_region_size(self.__n_profile_samples))

        recording = self.get_recording_sdram_usage(
            vertex_slice, machine_time_step)
        # build resources as i currently know
        container = ResourceContainer(
            sdram=recording + other,
            dtcm=DTCMResource(self.get_dtcm_usage_for_atoms()),
            cpu_cycles=CPUCyclesPerTickResource(
                self.get_cpu_usage_for_atoms()))

        return container

    @property
    def n_atoms(self):
        return self.__n_atoms

    @overrides(LegacyPartitionerAPI.create_machine_vertex)
    def create_machine_vertex(
            self, vertex_slice, resources_required, label=None,
            constraints=None):
        # pylint: disable=too-many-arguments, arguments-differ
        self.__n_subvertices += 1
        return SpikeSourcePoissonMachineVertex(
            resources_required, self.__spike_recorder.record,
            constraints, label, self, vertex_slice)

    @property
    def max_rate(self):
        return self.__max_rate

    @property
    def seed(self):
        return self.__seed

    @seed.setter
    def seed(self, seed):
        self.__seed = seed
        self.__kiss_seed = dict()
        self.__rng = None

    @overrides(AbstractSpikeRecordable.is_recording_spikes)
    def is_recording_spikes(self):
        return self.__spike_recorder.record

    @overrides(AbstractSpikeRecordable.set_recording_spikes)
    def set_recording_spikes(
            self, new_state=True, sampling_interval=None, indexes=None):
        if sampling_interval is not None:
            logger.warning("Sampling interval currently not supported for "
                           "SpikeSourcePoisson so being ignored")
        if indexes is not None:
            logger.warning("indexes not supported for "
                           "SpikeSourcePoisson so being ignored")
        if new_state and not self.__spike_recorder.record:
            self.__change_requires_mapping = True
        self.__spike_recorder.record = new_state

    @overrides(AbstractSpikeRecordable.get_spikes_sampling_interval)
    def get_spikes_sampling_interval(self):
        return globals_variables.get_simulator().machine_time_step

    @staticmethod
    def get_dtcm_usage_for_atoms():
        return 0

    @staticmethod
    def get_cpu_usage_for_atoms():
        return 0

    def kiss_seed(self, vertex_slice):
        if vertex_slice not in self.__kiss_seed:
            self.__kiss_seed[vertex_slice] = create_mars_kiss_seeds(
                self.__rng, self.__seed)
        return self.__kiss_seed[vertex_slice]

    def update_kiss_seed(self, vertex_slice, seed):
        """ updates a kiss seed from the machine

        :param vertex_slice: the vertex slice to update seed of
        :param seed: the seed
        :rtype: None
        """
        self.__kiss_seed[vertex_slice] = seed

    @overrides(AbstractSpikeRecordable.get_spikes)
    def get_spikes(self, placements, buffer_manager, machine_time_step):
        return self.__spike_recorder.get_spikes(
            self.label, buffer_manager,
            SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID,
            placements, self, machine_time_step)

    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [ContiguousKeyRangeContraint()]

    @overrides(AbstractSpikeRecordable.clear_spike_recording)
    def clear_spike_recording(self, buffer_manager, placements):
        for machine_vertex in self.machine_vertices:
            placement = placements.get_placement_of_vertex(machine_vertex)
            buffer_manager.clear_recorded_data(
                placement.x, placement.y, placement.p,
                SpikeSourcePoissonVertex.SPIKE_RECORDING_REGION_ID)

    def describe(self):
        """ Return a human-readable description of the cell or synapse type.

        The output may be customised by specifying a different template\
        together with an associated template engine\
        (see :py:mod:`pyNN.descriptions`).

        If template is None, then a dictionary containing the template context\
        will be returned.

        :rtype: dict(str, ...)
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
