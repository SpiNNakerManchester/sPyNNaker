# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import struct
import numpy
from spinn_front_end_common.utilities.helpful_functions import (
    locate_memory_region_for_placement)
from spinn_front_end_common.utilities.constants import BYTES_PER_WORD
from spynnaker.pyNN.exceptions import MemReadException

_RECORDING_COUNT = struct.Struct("<I")


def get_recording_region_size_in_bytes(
        n_machine_time_steps, bytes_per_timestep):
    """ Get the size of a recording region in bytes.

    :param int n_machine_time_steps:
    :param int bytes_per_timestep:
    :rtype: int
    """
    if n_machine_time_steps is None:
        raise Exception(
            "Cannot record this parameter without a fixed run time")
    return ((n_machine_time_steps * bytes_per_timestep) +
            (n_machine_time_steps * BYTES_PER_WORD))


def get_data(transceiver, placement, region, region_size):
    """ Get the recorded data from a region.

    :param ~spinnman.transceiver.Transceiver transceiver:
    :param ~pacman.model.placements.Placement placement:
    :param int region:
    :param int region_size:
    :rtype: tuple(bytearray, int)
    """

    region_base_address = locate_memory_region_for_placement(
        placement, region)
    number_of_bytes_written = transceiver.read_word(
        placement.x, placement.y, region_base_address)

    # Subtract 4 for the word representing the size itself
    expected_size = region_size - BYTES_PER_WORD
    if number_of_bytes_written > expected_size:
        raise MemReadException(
            "Expected {} bytes but read {}".format(
                expected_size, number_of_bytes_written))

    return (
        transceiver.read_memory(
            placement.x, placement.y, region_base_address + BYTES_PER_WORD,
            number_of_bytes_written),
        number_of_bytes_written)


def pull_off_cached_lists(no_loads, cache_file):
    """ Extracts numpy based data from a file

    :param int no_loads: the number of numpy elements in the file
    :param ~io.FileIO cache_file: the file to extract from
    :return: The extracted data
    :rtype: ~numpy.ndarray
    """
    cache_file.seek(0)
    if no_loads == 1:
        values = numpy.load(cache_file)
        # Seek to the end of the file (for windows compatibility)
        cache_file.seek(0, os.SEEK_END)
        return values
    elif no_loads == 0:
        return []

    lists = list()
    for _ in range(0, no_loads):
        lists.append(numpy.load(cache_file))
    # Seek to the end of the file (for windows compatibility)
    cache_file.seek(0, os.SEEK_END)
    return numpy.concatenate(lists)


def needs_buffering(buffer_max, space_needed, enable_buffered_recording):
    """
    :param int buffer_max:
    :param int space_needed:
    :param bool enable_buffered_recording:
    :rtype: bool
    """
    if space_needed == 0:
        return False
    if not enable_buffered_recording:
        return False
    if buffer_max < space_needed:
        return True
    return False


def get_buffer_sizes(buffer_max, space_needed, enable_buffered_recording):
    """
    :param int buffer_max:
    :param int space_needed:
    :param bool enable_buffered_recording:
    :rtype: int
    """
    if space_needed == 0:
        return 0
    if not enable_buffered_recording:
        return space_needed
    if buffer_max < space_needed:
        return buffer_max
    return space_needed


def make_missing_string(missing):
    """
    :param iterable(~pacman.model.placements.Placement) missing:
    :rtype: str
    """
    return "; ".join(
        "({}, {}, {})".format(placement.x, placement.y, placement.p)
        for placement in missing)
