from data_specification import utility_calls
from spynnaker.pyNN import exceptions

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
    return (_RECORDING_COUNT_SIZE +
            (n_machine_time_steps * bytes_per_timestep))


def get_data(transceiver, placement, region, region_size):
    """ Get the recorded data from a region
    """

    (x, y, p) = placement.x, placement.y, placement.p

    app_data_base_address = transceiver.get_cpu_information_from_core(
        x, y, p).user[0]
    region_base_address_offset = utility_calls.get_region_base_address_offset(
        app_data_base_address, region)
    region_base_address_buf = buffer(transceiver.read_memory(
        x, y, region_base_address_offset, 4))
    region_base_address = struct.unpack_from("<I", region_base_address_buf)[0]
    region_base_address += app_data_base_address
    number_of_bytes_written_buf = buffer(transceiver.read_memory(
        x, y, region_base_address, 4))
    number_of_bytes_written = struct.unpack_from(
        "<I", number_of_bytes_written_buf)[0]

    # Subtract 4 for the word representing the size itself
    expected_size = region_size - _RECORDING_COUNT_SIZE
    if number_of_bytes_written > expected_size:
        raise exceptions.MemReadException(
            "Expected {} bytes but read {}".format(
                expected_size, number_of_bytes_written))

    return transceiver.read_memory(
        x, y, region_base_address + 4, number_of_bytes_written), \
           number_of_bytes_written


def pull_off_cached_lists(no_loads, cache_file):
    """
    helper method for extracting numpy based data froma  file
    :param no_loads: the numebr of numpy elements in the file
    :param cache_file: the file to extract from
    :return:
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
