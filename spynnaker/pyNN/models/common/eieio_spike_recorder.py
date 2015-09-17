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

        # A list of tuples of (placement, vertex_slice)
        self._subvertex_information = list()

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, record):
        self._record = record

    def add_subvertex_information(
            self, placement, vertex_slice, base_key, region_size):
        """ Add a subvertex for spike retrieval
        """
        self._subvertex_information.append(
            (placement, vertex_slice, base_key, region_size))

    def get_dtcm_usage_in_bytes(self):
        if not self._record:
            return 0
        return 4

    def get_n_cpu_cycles(self, n_neurons):
        if not self._record:
            return 0
        return n_neurons * 4

    def get_spikes(self, label, transceiver, region):
        ms_per_tick = self._machine_time_step / 1000.0
        progress_bar = ProgressBar(len(self._subvertex_information),
                                   "Getting spikes for {}".format(label))
        results = list()
        for (placement, subvertex_slice,
                base_key, region_size) in self._subvertex_information:

            # Read the spikes
            spike_data = recording_utils.get_data(
                transceiver, placement, region, region_size)

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
                neuron_ids = (keys - base_key) + subvertex_slice.lo_atom
                offset += eieio_header.count * 4
                results.append(numpy.dstack((neuron_ids, timestamps))[0])
            progress_bar.update()

        progress_bar.end()
        result = numpy.vstack(results)
        result = result[numpy.lexsort((result[:, 1], result[:, 0]))]
        return result
