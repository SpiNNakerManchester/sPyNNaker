from spinn_front_end_common.utilities import helpful_functions
from spynnaker.pyNN.exceptions import MemReadException

import struct
import logging
import numpy

logger = logging.getLogger(__name__)

_RECORDING_COUNT_SIZE = 4


def get_recording_region_size_in_bytes(
        n_machine_time_steps, bytes_per_timestep):
    """ Get the size of a recording region in bytes
    """
    if n_machine_time_steps is None:
        raise Exception(
            "Cannot record this parameter without a fixed run time")
    return ((n_machine_time_steps * bytes_per_timestep) +
            (n_machine_time_steps * 4))


def get_data(transceiver, placement, region, region_size):
    """ Get the recorded data from a region
    """

    region_base_address = helpful_functions.locate_memory_region_on_core(
        placement.x, placement.y, placement.p, region, transceiver)
    number_of_bytes_written_buf = buffer(transceiver.read_memory(
        placement.x, placement.y, region_base_address, 4))
    number_of_bytes_written = struct.unpack_from(
        "<I", number_of_bytes_written_buf)[0]

    # Subtract 4 for the word representing the size itself
    expected_size = region_size - _RECORDING_COUNT_SIZE
    if number_of_bytes_written > expected_size:
        raise MemReadException(
            "Expected {} bytes but read {}".format(
                expected_size, number_of_bytes_written))

    return (
        transceiver.read_memory(
            placement.x, placement.y, region_base_address + 4,
            number_of_bytes_written),
        number_of_bytes_written)


def pull_off_cached_lists(no_loads, cache_file):
    """ Extracts numpy based data from a  file

    :param no_loads: the number of numpy elements in the file
    :param cache_file: the file to extract from
    :return: The extracted data
    """
    cache_file.seek(0)
    if no_loads == 1:
        values = numpy.load(cache_file)

        # Seek to the end of the file (for windows compatibility)
        cache_file.seek(0, 2)
        return values
    elif no_loads == 0:
        return []
    else:
        lists = list()
        for _ in range(0, no_loads):
            lists.append(numpy.load(cache_file))

        # Seek to the end of the file (for windows compatibility)
        cache_file.seek(0, 2)
        return numpy.concatenate(lists)


def needs_buffering(buffer_max, space_needed, enable_buffered_recording):
    if space_needed == 0:
        return False
    if not enable_buffered_recording:
        return False
    if buffer_max < space_needed:
        return True
    return False


def get_buffer_sizes(buffer_max, space_needed, enable_buffered_recording):
    if space_needed == 0:
        return 0
    if not enable_buffered_recording:
        return space_needed
    if buffer_max < space_needed:
        return buffer_max
    return space_needed
