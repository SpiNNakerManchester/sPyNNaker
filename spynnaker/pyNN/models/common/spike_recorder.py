from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spynnaker.pyNN.models.common import recording_utils

import math
import numpy


class SpikeRecorder(object):

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record = False

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

    def get_spikes(self, label, transceiver, region, n_machine_time_steps,
                   placements, graph_mapper, partitionable_vertex):

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
            region_size = recording_utils.get_recording_region_size_in_bytes(
                n_machine_time_steps, n_bytes)
            spike_data = recording_utils.get_data(
                transceiver, placement, region, region_size)
            numpy_data = numpy.asarray(spike_data, dtype="uint8").view(
                dtype="uint32").byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(numpy_data).reshape(
                (-1, 32))).reshape((-1, n_bytes * 8))
            times, indices = numpy.where(bits == 1)
            times = times * ms_per_tick
            indices = indices + lo_atom
            spike_ids.append(indices)
            spike_times.append(times)
            progress_bar.update()

        progress_bar.end()
        spike_ids = numpy.hstack(spike_ids)
        spike_times = numpy.hstack(spike_times)
        result = numpy.dstack((spike_ids, spike_times))[0]
        return result[numpy.lexsort((spike_times, spike_ids))]
