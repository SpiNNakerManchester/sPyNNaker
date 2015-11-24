from pacman.utilities.utility_objs.progress_bar import ProgressBar
from spinnman.messages.eieio.data_messages.eieio_data_header \
    import EIEIODataHeader

import numpy

import logging

logger = logging.getLogger(__name__)


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
                   placements, graph_mapper, partitionable_vertex,
                   base_key_function):

        results = list()
        missing = list()
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
            raw_spike_data, missing_processor = \
                buffer_manager.get_data_for_vertex(
                    x, y, p, region, state_region)
            if missing_processor is not None:
                missing.append(missing_processor)
            spike_data = raw_spike_data.read_all()
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
                neuron_ids = ((keys - base_key_function(subvertex)) +
                              subvertex_slice.lo_atom)
                offset += eieio_header.count * 4
                results.append(numpy.dstack((neuron_ids, timestamps))[0])
            progress_bar.update()

        progress_bar.end()
        for i in missing:
            logger.info(
                "Missing information in chip ({0:d},{1:d}), core {2:d},"
                "population {3:s}, for region {4:d}".format(
                    i[0], i[1], i[2], label, i[3]))
        if len(results) != 0:
            result = numpy.vstack(results)
            result = result[numpy.lexsort((result[:, 1], result[:, 0]))]
        else:
            result = []
        return result
