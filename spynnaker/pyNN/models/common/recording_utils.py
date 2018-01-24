from __future__ import division
import struct
import logging
import numpy

from data_specification.enums import DataType
from spinn_front_end_common.utilities import exceptions as fec_excceptions
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.helpful_functions \
    import locate_memory_region_for_placement
from spynnaker.pyNN.exceptions import MemReadException
from spynnaker.pyNN.models.neural_properties import NeuronParameter


MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

logger = logging.getLogger(__name__)
_RECORDING_COUNT = struct.Struct("<I")


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

    region_base_address = locate_memory_region_for_placement(
        placement, region, transceiver)
    number_of_bytes_written_buf = buffer(transceiver.read_memory(
        placement.x, placement.y, region_base_address, 4))
    number_of_bytes_written = _RECORDING_COUNT.unpack_from(
        number_of_bytes_written_buf)[0]

    # Subtract 4 for the word representing the size itself
    expected_size = region_size - _RECORDING_COUNT.size
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


def compute_rate(new_state, sampling_interval):
    """
    Converts a simpling interval into a rate

    Remember machine time step is in nano seconds

    :param sampling_interval: interval between samples in micro seconds
    :return: rate
    """
    if new_state:
        if sampling_interval is None:
            return 1

        step = globals_variables.get_simulator().machine_time_step / 1000
        rate = int(sampling_interval / step)
        if sampling_interval != rate * step:
            msg = "sampling_interval {} is not an an integer " \
                  "multiple of the simulation timestep {}" \
                  "".format(sampling_interval, step)
            raise fec_excceptions.ConfigurationException(msg)
        if rate > MAX_RATE:
            msg = "sampling_interval {} higher than max allowed which is {}" \
                  "".format(sampling_interval, step * MAX_RATE)
            raise fec_excceptions.ConfigurationException(msg)
        return rate

    else:
        return 0


def compute_interval(sampling_rate):
    """

    :param sampling_rate:
    :return:
    """
    step = globals_variables.get_simulator().machine_time_step / 1000
    return sampling_rate * step


def rate_parameter(sampling_rate):
    return NeuronParameter(sampling_rate, DataType.UINT32)
