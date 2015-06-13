from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.utilities import constants
from spynnaker.pyNN import exceptions

from data_specification import utility_calls as dsg_utility_calls

import logging
import numpy
import struct
import math
from collections import OrderedDict

logger = logging.getLogger(__name__)


class AbstractSpikeRecordableVertex(object):
    """ An object which records spikes using a bit vector of 32-bit words
    """

    def __init__(self, label, machine_time_step):
        self._record = False
        self._label = label
        self._machine_time_step = machine_time_step
        self._spike_recordable_subvertices = OrderedDict()

    @property
    def record(self):
        """ True if recording is enabled
        """
        return self._record

    def set_record(self, record):
        """ Set the recording of spikes
        """
        self._record = record

    @staticmethod
    def _get_spike_bytes_per_time_step(vertex_slice):
        return int(math.ceil(vertex_slice.n_atoms / 32.0)) * 4

    @staticmethod
    def get_spike_recording_region_size(n_machine_time_steps,
                                        vertex_slice):
        """ Get the size of the spike recording region in bytes
        """
        bytes_per_time_step = \
            AbstractSpikeRecordableVertex._get_spike_bytes_per_time_step(
                vertex_slice)
        return (constants.RECORDING_ENTRY_BYTE_SIZE +
                (n_machine_time_steps * bytes_per_time_step))

    def add_spike_recordable_subvertex(self, subvertex, vertex_slice):
        """ Used to keep track of the spike recordable subvertices of this
            vertex, to allow the retrieving of the recorded data
        """
        self._spike_recordable_subvertices[subvertex] = vertex_slice

    def get_spikes(self, placements, transciever, compatible_output,
                   n_machine_time_steps):
        """ Get a 2-column numpy array containing cell ids and spike times for
            recorded cells.\
            This is read directly from the memory for the board.
        """

        spike_times = list()
        spike_ids = list()
        ms_per_tick = self._machine_time_step / 1000.0

        # Find all the sub-vertices that this pynn_population.py exists on
        progress_bar = ProgressBar(len(self._spike_recordable_subvertices),
                                   "Getting spikes for {}".format(self._label))
        for subvertex, subvertex_slice in self._spike_recordable_subvertices:
            spike_recording_region = subvertex.get_spike_recording_region()
            placement = placements.get_placement_of_subvertex(subvertex)
            (x, y, p) = placement.x, placement.y, placement.p
            lo_atom = subvertex_slice.lo_atom
            logger.debug("Reading spikes from chip {}, {}, core {}, "
                         "lo_atom {}".format(x, y, p, lo_atom))

            # Get the App Data for the core
            app_data_base_address = transciever.get_cpu_information_from_core(
                x, y, p).user[0]

            # Get the position of the spike buffer
            spike_region_base_address_offset = \
                dsg_utility_calls.get_region_base_address_offset(
                    app_data_base_address, spike_recording_region)
            spike_region_base_address_buf = str(list(transciever.read_memory(
                x, y, spike_region_base_address_offset, 4))[0])
            spike_region_base_address = struct.unpack(
                "<I", spike_region_base_address_buf)[0]
            spike_region_base_address += app_data_base_address

            # Read the spike data size
            number_of_bytes_written_buf = str(list(transciever.read_memory(
                x, y, spike_region_base_address, 4))[0])
            number_of_bytes_written = struct.unpack_from(
                "<I", number_of_bytes_written_buf)[0]

            # check that the number of spikes written is smaller or the same as
            # the size of the memory region we allocated for spikes
            size_of_region = \
                AbstractSpikeRecordableVertex.get_spike_recording_region_size(
                    n_machine_time_steps, subvertex_slice)
            if number_of_bytes_written > size_of_region:
                raise exceptions.MemReadException(
                    "the amount of memory written ({}) was larger than was "
                    "allocated for it ({})"
                    .format(number_of_bytes_written, size_of_region))

            # Read the spikes
            logger.debug("Reading {} ({}) bytes starting at {} + 4"
                         .format(number_of_bytes_written,
                                 hex(number_of_bytes_written),
                                 hex(spike_region_base_address)))
            spike_data = transciever.read_memory(
                x, y, spike_region_base_address + 4, number_of_bytes_written)

            data_list = bytearray()
            for data in spike_data:
                data_list.extend(data)

            numpy_data = numpy.asarray(data_list, dtype="uint8").view(
                dtype="<i4").byteswap().view("uint8")
            bits = numpy.fliplr(numpy.unpackbits(numpy_data).reshape(
                (-1, 32))).reshape((-1, self._get_spike_bytes_per_time_step(
                    subvertex_slice) * 8))
            indices = [numpy.add(numpy.where(items)[0], lo_atom)
                       for items in bits]
            times = [numpy.repeat(i * ms_per_tick, len(indices[i]))
                     for i in range(len(indices))]
            spike_ids.extend([item for sublist in indices for item in sublist])
            spike_times.extend([item for sublist in times for item in sublist])
            progress_bar.update()

        progress_bar.end()
        result = numpy.dstack((spike_ids, spike_times))[0]

        # check before doing lexsort that there is data to sort,
        # otherwise numpy blows up.
        if len(spike_ids) > 1:
            result = result[numpy.lexsort((spike_times, spike_ids))]
        return result
