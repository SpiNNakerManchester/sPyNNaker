"""

"""
import logging

from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex

from spynnaker.pyNN.models.common.abstract_spike_recordable_vertex \
    import AbstractSpikeRecordableVertex
from spynnaker.pyNN.utilities import utility_calls
from spynnaker.pyNN.models.spike_source.\
    spike_source_poisson_partitioned_vertex \
    import SpikeSourcePoissonPartitionedVertex

from spinn_front_end_common.interface.has_n_machine_timesteps \
    import HasNMachineTimesteps
from spinn_front_end_common.utilities import simulation_utilities
from spinn_front_end_common.abstract_models.\
    abstract_data_specable_partitioned_vertex \
    import AbstractDataSpecablePartitionedVertex

logger = logging.getLogger(__name__)

PARAMS_BASE_WORDS = 4
PARAMS_WORDS_PER_NEURON = 5
RANDOM_SEED_WORDS = 4


class SpikeSourcePoisson(
        AbstractSpikeRecordableVertex, AbstractPartitionableVertex,
        AbstractDataSpecablePartitionedVertex, HasNMachineTimesteps):
    """ A Poisson Spike source model
    """

    _model_based_max_atoms_per_core = 256

    def __init__(self, n_keys, machine_time_step, timescale_factor,
                 spikes_per_second, ring_buffer_sigma,
                 constraints=None, label="SpikeSourcePoisson",
                 rate=1.0, start=0.0, duration=None, seed=None):
        """
        """
        utility_calls.unused(spikes_per_second)
        utility_calls.unused(ring_buffer_sigma)

        AbstractSpikeRecordableVertex.__init__(self, label, machine_time_step)
        AbstractPartitionableVertex.__init__(
            self, n_atoms=n_keys, label=label, constraints=constraints,
            max_atoms_per_core=self._model_based_max_atoms_per_core)
        AbstractDataSpecablePartitionedVertex.__init__(self)
        HasNMachineTimesteps.__init__(self)
        self._rate = rate
        self._start = start
        self._duration = duration
        self._seed = seed

        if duration is None:
            self._duration = ((4294967295.0 - self._start) /
                              (1000.0 * machine_time_step))

    @property
    def model_name(self):
        """
        """
        return "SpikeSourcePoisson"

    @staticmethod
    def set_model_max_atoms_per_core(new_value):
        """
        """
        SpikeSourcePoisson.\
            _model_based_max_atoms_per_core = new_value

    @staticmethod
    def get_params_bytes(vertex_slice):
        """ Get the size of the possion parameters in bytes

        :param vertex_slice:
        """
        return (RANDOM_SEED_WORDS + PARAMS_BASE_WORDS +
                (((vertex_slice.hi_atom - vertex_slice.lo_atom) + 1) *
                 PARAMS_WORDS_PER_NEURON)) * 4

    # inherited from partionable vertex
    def get_sdram_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        poisson_params_sz = self.get_params_bytes(vertex_slice)
        spike_hist_buff_sz = 0
        if self.record:
            spike_hist_buff_sz = self.get_spike_recording_region_size(
                self.n_machine_timesteps, vertex_slice)(vertex_slice)
        return (simulation_utilities.HEADER_REGION_BYTES +
                poisson_params_sz + spike_hist_buff_sz)

    def get_dtcm_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        return 0

    def get_cpu_usage_for_atoms(self, vertex_slice, graph):
        """
        """
        return 0

    def create_subvertex(self, vertex_slice, resources_required, label=None,
                         constraints=None):
        subvertex = SpikeSourcePoissonPartitionedVertex(
            resources_required, label, constraints,
            self, vertex_slice, self._machine_time_step,
            self._timescale_factor, self._record)
        AbstractSpikeRecordableVertex.add_spike_recordable_subvertex(
            self, subvertex, vertex_slice)
        return subvertex
