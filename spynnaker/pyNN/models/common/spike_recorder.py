from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import math
import numpy
import tempfile

class SpikeRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record = False
        # set up cache files for recording of parameters
        self._spikes_cache_file = None
        # position params for knowing how much data has been extracted
        self._extracted_spike_machine_time_steps = 0
        # number of times the spikes have been loaded to the temp file
        self._no_spike_loads = 0

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def get_sdram_usage_in_bytes(
            self, n_neurons, n_machine_time_steps):
        if not self._record:
            return 0

        out_spike_bytes = int(math.ceil(n_neurons / 32.0)) * 4
        return recording_utils.get_recording_region_size_in_bytes(
            n_machine_time_steps, out_spike_bytes)

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def reset(self):
        self._spikes_cache_file = None
        self._extracted_spike_machine_time_steps = 0
        self._no_spike_loads = 0

    def get_spikes(self, label, transceiver, region, n_machine_time_steps,
                   placements, graph_mapper, partitionable_vertex,
                   return_data=True):

        if self._spikes_cache_file is None:
            self._spikes_cache_file = tempfile.NamedTemporaryFile(mode='a+b')

        if n_machine_time_steps == self._extracted_spike_machine_time_steps:
            if return_data:
                return recording_utils.pull_off_cached_lists(
                    self._no_spike_loads, self._spikes_cache_file)
        else:
            to_extract_n_machine_time_steps = \
                n_machine_time_steps - self._extracted_spike_machine_time_steps

            spike_times = list()
            spike_ids = list()
            ms_per_tick = self._machine_time_step / 1000.0

            subvertices = \
                graph_mapper.get_subvertices_from_vertex(partitionable_vertex)

            progress_bar = ProgressBar(len(subvertices),
                                       "Getting spikes for {}".format(label))
            for subvertex in subvertices:

                placement = placements.get_placement_of_subvertex(subvertex)
                subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)

                lo_atom = subvertex_slice.lo_atom

                # Read the spikes
                n_bytes = int(math.ceil(subvertex_slice.n_atoms / 32.0)) * 4
                region_size = \
                    recording_utils.get_recording_region_size_in_bytes(
                        to_extract_n_machine_time_steps, n_bytes)
                spike_data, number_bytes_written = recording_utils.get_data(
                    transceiver, placement, region, region_size)
                numpy_data = numpy.asarray(spike_data, dtype="uint8").view(
                    dtype="uint32").byteswap().view("uint8")
                bits = numpy.fliplr(numpy.unpackbits(numpy_data).reshape(
                    (-1, 32))).reshape((-1, n_bytes * 8))
                times, indices = numpy.where(bits == 1)
                times = ((times +
                         self._extracted_spike_machine_time_steps) *
                         ms_per_tick)
                indices = indices + lo_atom
                spike_ids.append(indices)
                spike_times.append(times)
                progress_bar.update()

            progress_bar.end()
            spike_ids = numpy.hstack(spike_ids)
            spike_times = numpy.hstack(spike_times)
            if len(spike_times) == 0 or len(spike_ids) == 0:
                # extract old data
                cached_spikes = recording_utils.pull_off_cached_lists(
                    self._no_spike_loads, self._spikes_cache_file)
                self._extracted_spike_machine_time_steps += \
                    to_extract_n_machine_time_steps
                return cached_spikes
            else:
                result = numpy.dstack((spike_ids, spike_times))[0]
                spikes = result[numpy.lexsort((spike_times, spike_ids))]

                # extract old data
                cached_spikes = recording_utils.pull_off_cached_lists(
                    self._no_spike_loads, self._spikes_cache_file)

                # cache the data just pulled off
                numpy.save(self._spikes_cache_file, spikes)
                self._no_spike_loads += 1

                # concat extracted with cached
                if len(cached_spikes) != 0:
                    all_spikes = numpy.concatenate((cached_spikes, spikes))
                else:
                    all_spikes = spikes

                self._extracted_spike_machine_time_steps += \
                    to_extract_n_machine_time_steps

                # return all spikes
                return all_spikes

