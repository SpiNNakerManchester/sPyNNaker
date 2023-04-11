# Copyright (c) 2021 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from spynnaker.pyNN.utilities.utility_calls import moved_in_v6
from spynnaker.pyNN.utilities.neo_convertor import (
    convert_analog_signal as _convert_analog_signal,
    convert_data as _convert_data,
    convert_data_list as _convert_data_list,
    convert_gsyn as _convert_gsyn,
    convert_spikes as _convert_spikes,
    convert_spiketrains as _convert_spiketrains)


def convert_analog_signal(signal_array, time_unit):
    """
    Converts part of a NEO object into told spynnaker7 format.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.AnalogSignal signal_array: Extended Quantities object
    :param quantities.unitquantity.UnitTime time_unit:
        Data time unit for time index
    :rtype: ~numpy.ndarray
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_analog_signal(signal_array, time_unit)


def convert_data(data, name, run=0):
    """
    Converts the data into a numpy array in the format ID, time, value.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block data: Data as returned by a getData() call
    :param str name: Name of the data to be extracted.
        Same values as used in getData()
    :param int run: Zero based index of the run to extract data for
    :rtype: ~numpy.ndarray
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_data(data, name, run)


def convert_data_list(data, name, runs=None):
    """
    Converts the data into a list of numpy arrays in the format ID, time,
    value.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block data: Data as returned by a getData() call
    :param str name: Name of the data to be extracted.
        Same values as used in getData()
    :param runs: List of Zero based index of the run to extract data for.
        Or None to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_data_list(data, name, runs)


def convert_v_list(data, runs=None):
    """
    Converts the voltage into a list numpy array one per segment (all runs)
    in the format ID, time, value.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block data: The data to convert; it must have V data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or None to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_data_list(data, "v", runs=runs)


def convert_gsyn_exc_list(data, runs=None):
    """
    Converts the gsyn_exc into a list numpy array one per segment (all runs)
    in the format ID, time, value.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block data:
        The data to convert; it must have Gsyn_exc data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or None to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_data_list(data, "gsyn_exc", runs=runs)


def convert_gsyn_inh_list(data, runs=None):
    """
    Converts the gsyn_inh into a list numpy array one per segment (all runs)
    in the format ID, time, value.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block data:
        The data to convert; it must have Gsyn_inh data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or None to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_data_list(data, "gsyn_inh", runs=runs)


def convert_gsyn(gsyn_exc, gsyn_inh):
    """
    Converts two neo objects into the spynnaker7 format.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block gsyn_exc: neo with gsyn_exc data
    :param ~neo.core.Block gsyn_inh: neo with gsyn_exc data
    :rtype: ~numpy.ndarray
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_gsyn(gsyn_exc, gsyn_inh)


def convert_spiketrains(spiketrains):
    """
    Converts a list of spiketrains into spynnaker7 format.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param list(~neo.core.SpikeTrain) spiketrains: List of SpikeTrains
    :rtype: ~numpy.ndarray
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_spiketrains(spiketrains)


def convert_spikes(neo, run=0):
    """
    Extracts the spikes for run one from a Neo Object.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block neo: neo Object including Spike Data
    :param int run: Zero based index of the run to extract data for
    :rtype: ~numpy.ndarray
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return _convert_spikes(neo, run)


def count_spiketrains(spiketrains):
    """
    Help function to count the number of spikes in a list of spiketrains.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param list(~neo.core.SpikeTrain) spiketrains: List of SpikeTrains
    :return: Total number of spikes in all the spiketrains
    :rtype: int
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return sum(map(len, spiketrains))


def count_spikes(neo):
    """
    Help function to count the number of spikes in a list of spiketrains.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.utilities.neo_convertor` instead.

    :param ~neo.core.Block neo: Neo Object which has spikes in it
    :return: The number of spikes in the first segment
    """
    moved_in_v6(
        "spynnaker8.utilities.neo_convertor",
        "spynnaker.pyNN.utilities.neo_convertor")
    return count_spiketrains(neo.segments[0].spiketrains)
