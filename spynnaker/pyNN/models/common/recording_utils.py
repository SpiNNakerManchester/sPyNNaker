from spinn_front_end_common.utilities import helpful_functions
from spynnaker.pyNN import exceptions

import struct
import logging

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

    region_base_address = helpful_functions.get_region_address(
        transceiver, placement, region)
    number_of_bytes_written_buf = buffer(transceiver.read_memory(
        placement.x, placement.y, region_base_address, 4))
    number_of_bytes_written = struct.unpack_from(
        "<I", number_of_bytes_written_buf)[0]

    # Subtract 4 for the word representing the size itself
    expected_size = region_size - _RECORDING_COUNT_SIZE
    if number_of_bytes_written > expected_size:
        raise exceptions.MemReadException(
            "Expected {} bytes but read {}".format(
                expected_size, number_of_bytes_written))

    return transceiver.read_memory(
        placement.x, placement.y, region_base_address + 4,
        number_of_bytes_written)
