from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spinnman.messages.eieio.data_messages.eieio_data_header \
    import EIEIODataHeader
from spynnaker.pyNN.models.common import recording_utils

import numpy


class EIEIOSpikeRecorder(object):
    """ Records spikes using EIEIO format
    """

    def __init__(self, machine_time_step):
        self._machine_time_step = machine_time_step
        self._record = False
        # set up cache files for recording of parameters
        self._spikes_cache_file = None
        # position params for knowing how much data has been extracted
        self._extracted_spike_machine_time_steps = 0
        # number of times the spikes have been loaded to the temp file
        self._no_spike_loads = 0

    def reset(self):
        self._spikes_cache_file = None
        self._extracted_spike_machine_time_steps = 0
        self._no_spike_loads = 0

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def get_spikes(self, label, transceiver, region, n_machine_time_steps,
                   placements, graph_mapper, partitionable_vertex,
                   return_data=True):

        if n_machine_time_steps == self._extracted_spike_machine_time_steps:
            if return_data:
                return recording_utils.pull_off_cached_lists(
                    self._no_spike_loads, self._spikes_cache_file)
        else:
            self._extracted_spike_machine_time_steps += n_machine_time_steps

            results = list()
            ms_per_tick = self._machine_time_step / 1000.0
            subvertices = \
                graph_mapper.get_subvertices_from_vertex(partitionable_vertex)
            progress_bar = ProgressBar(len(subvertices),
                                       "Getting spikes for {}".format(label))

            for subvertex in subvertices:

                placement = placements.get_placement_of_subvertex(subvertex)
                subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)

                # Read the spikes
                spike_data, number_of_bytes_written = recording_utils.get_data(
                    transceiver, placement, region, subvertex.region_size)

                offset = 0
                while offset < number_of_bytes_written:
                    eieio_header = EIEIODataHeader.from_bytestring(
                        spike_data, offset)
                    offset += eieio_header.size
                    timestamp = eieio_header.payload_base * ms_per_tick
                    timestamps = numpy.repeat([timestamp], eieio_header.count)
                    keys = numpy.frombuffer(
                        spike_data, dtype="<u4", count=eieio_header.count,
                        offset=offset)
                    neuron_ids = \
                        (keys - subvertex.base_key) + subvertex_slice.lo_atom
                    offset += eieio_header.count * 4
                    results.append(numpy.dstack((neuron_ids, timestamps))[0])
                progress_bar.update()

            progress_bar.end()
            result = numpy.vstack(results)
            spikes = result[numpy.lexsort((result[:, 1], result[:, 0]))]

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

            # return all spikes
            return all_spikes
