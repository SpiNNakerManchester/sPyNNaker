from pacman.utilities.progress_bar import ProgressBar
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

    def get_spikes(self, label, buffer_manager, region, state_region,
                   placements, graph_mapper, partitionable_vertex):

        results = list()
        ms_per_tick = self._machine_time_step / 1000.0
        subvertices = \
            graph_mapper.get_subvertices_from_vertex(partitionable_vertex)
        progress_bar = ProgressBar(len(subvertices),
                                   "Getting spikes for {}".format(label))

        for subvertex in subvertices:

            placement = placements.get_placement_of_subvertex(subvertex)
            subvertex_slice = graph_mapper.get_subvertex_slice(subvertex)

            x = placement.x
            y = placement.y
            p = placement.p
            # Read the spikes
#            spike_data = recording_utils.get_data(
#                transceiver, placement, region, subvertex.region_size)
            spike_data = buffer_manager.get_data_for_vertex(
                x, y, p, region, state_region)

            number_of_bytes_written = len(spike_data)

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
        result = result[numpy.lexsort((result[:, 1], result[:, 0]))]
        return result
