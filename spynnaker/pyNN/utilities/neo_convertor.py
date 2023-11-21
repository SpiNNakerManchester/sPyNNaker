# Copyright (c) 2017 The University of Manchester
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

import quantities
from quantities import UnitTime
import numpy as np
from numpy.typing import NDArray
from neo import AnalogSignal, Block, SpikeTrain
from typing import List, Optional, Sequence

# needed as dealing with quantities
# pylint: disable=c-extension-no-member


def convert_analog_signal(
        signal_array: AnalogSignal,
        time_unit: UnitTime = quantities.ms) -> NDArray:
    """
    Converts part of a NEO object into told spynnaker7 format.

    :param ~neo.core.AnalogSignal signal_array: Extended Quantities object
    :param quantities.unitquantity.UnitTime time_unit:
        Data time unit for time index
    :rtype: ~numpy.ndarray
    """
    ids = signal_array.annotations["channel_names"]
    xs = range(len(ids))
    if time_unit == quantities.ms:
        times = signal_array.times.magnitude
    else:
        times = signal_array.times.rescale(time_unit).magnitude
    all_times = np.tile(times, len(xs))
    neurons = np.repeat(ids, len(times))
    values = np.concatenate([signal_array.magnitude[:, x] for x in xs])
    return np.column_stack((neurons, all_times, values))


def convert_data(data: Block, name: str, run: int = 0) -> NDArray:
    """
    Converts the data into a numpy array in the format ID, time, value.

    :param ~neo.core.Block data: Data as returned by a getData() call
    :param str name: Name of the data to be extracted.
        Same values as used in getData()
    :param int run: Zero based index of the run to extract data for
    :rtype: ~numpy.ndarray
    """
    if len(data.segments) <= run:
        raise ValueError(
            f"Data only contains {len(data.segments)} so unable to run {run}. "
            "Note run is the zero based index.")
    if name == "all":
        raise ValueError("Unable to convert all data in one go "
                         "as result would be comparing apples and oranges.")
    if name == "spikes":
        return convert_spikes(data, run)
    return convert_analog_signal(
        data.segments[run].filter(name=name)[0])


def convert_data_list(data: Block, name: str,
                      runs: Optional[Sequence[int]] = None) -> List[NDArray]:
    """
    Converts the data into a list of numpy arrays in the format ID, time,
    value.

    :param ~neo.core.Block data: Data as returned by a getData() call
    :param str name: Name of the data to be extracted.
        Same values as used in getData()
    :param runs: List of Zero based index of the run to extract data for.
        Or `None` to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    if runs is None:
        runs = range(len(data.segments))
    return [
        convert_data(data, name, run=run)
        for run in runs]


def convert_v_list(
        data: Block, runs: Optional[Sequence[int]] = None) -> List[NDArray]:
    """
    Converts the voltage into a list numpy array one per segment (all
    runs) in the format ID, time, value.

    :param ~neo.core.Block data: The data to convert; it must have V data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or `None` to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    return convert_data_list(data, "v", runs=runs)


def convert_gsyn_exc_list(
        data: Block, runs: Optional[Sequence[int]] = None) -> List[NDArray]:
    """
    Converts the gsyn_exc into a list numpy array one per segment (all
    runs) in the format ID, time, value.

    :param ~neo.core.Block data:
        The data to convert; it must have Gsyn_exc data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or `None` to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    return convert_data_list(data, "gsyn_exc", runs=runs)


def convert_gsyn_inh_list(
        data: Block, runs: Optional[Sequence[int]] = None) -> List[NDArray]:
    """
    Converts the gsyn_inh into a list numpy array one per segment (all
    runs) in the format ID, time, value.

    :param ~neo.core.Block data:
        The data to convert; it must have Gsyn_inh data in it
    :param runs: List of Zero based index of the run to extract data for.
        Or `None` to extract all runs
    :type runs: list(int) or None
    :rtype: list(~numpy.ndarray)
    """
    return convert_data_list(data, "gsyn_inh", runs=runs)


def convert_gsyn(gsyn_exc: Block, gsyn_inh: Block) -> NDArray:
    """
    Converts two neo objects into the spynnaker7 format.

    .. note::
        It is acceptable for both neo parameters to be the same object

    :param ~neo.core.Block gsyn_exc: neo with gsyn_exc data
    :param ~neo.core.Block gsyn_inh: neo with gsyn_exc data
    :rtype: ~numpy.ndarray
    """
    exc = gsyn_exc.segments[0].filter(name='gsyn_exc')[0]
    inh = gsyn_inh.segments[0].filter(name='gsyn_inh')[0]
    ids = exc.annotations["channel_names"]
    ids2 = inh.annotations["channel_names"]
    if len(ids) != len(ids2):
        raise ValueError(
            f"Found {len(ids)} neuron IDs in gsyn_exc "
            f"but {len(ids2)} in gsyn_inh")
    if not np.allclose(ids, ids2):
        raise ValueError("IDs in gsyn_exc and gsyn_inh do not match")
    times = exc.times.rescale(quantities.ms)
    times2 = inh.times.rescale(quantities.ms)
    if len(times) != len(times2):
        raise ValueError(
            f"Found {len(times)} times in gsyn_exc "
            f"but {len(times2)} in gsyn_inh")
    if not np.allclose(times, times2):
        raise ValueError("times in gsyn_exc and gsyn_inh do not match")
    all_times = np.tile(times, len(ids))
    neurons = np.repeat(ids, len(times))
    exc_np = np.concatenate([exc[:, x] for x in range(len(ids))])
    inh_np = np.concatenate([inh[:, x] for x in range(len(ids))])
    return np.column_stack((neurons, all_times, exc_np, inh_np))


def convert_spiketrains(spiketrains: List[SpikeTrain]) -> NDArray:
    """
    Converts a list of spiketrains into spynnaker7 format.

    :param list(~neo.core.SpikeTrain) spiketrains: List of SpikeTrains
    :rtype: ~numpy.ndarray
    """
    if len(spiketrains) == 0:
        return np.empty(shape=(0, 2))

    neurons = np.concatenate([
        np.repeat(x.annotations['source_index'], len(x))
        for x in spiketrains])
    spikes = np.concatenate([x.magnitude for x in spiketrains])
    return np.column_stack((neurons, spikes))


def convert_spikes(neo: Block, run: int = 0) -> NDArray:
    """
    Extracts the spikes for run one from a Neo Object.

    :param ~neo.core.Block neo: neo Object including Spike Data
    :param int run: Zero based index of the run to extract data for
    :rtype: ~numpy.ndarray
    """
    if len(neo.segments) <= run:
        raise ValueError(
            f"Data only contains {len(neo.segments)} so unable to run {run}. "
            "Note run is the zero based index.")
    return convert_spiketrains(neo.segments[run].spiketrains)


def count_spiketrains(spiketrains: SpikeTrain) -> int:
    """
    Help function to count the number of spikes in a list of spiketrains.

    :param list(~neo.core.SpikeTrain) spiketrains: List of SpikeTrains
    :return: Total number of spikes in all the spiketrains
    :rtype: int
    """
    return sum(map(len, spiketrains))


def count_spikes(neo: Block) -> int:
    """
    Help function to count the number of spikes in a list of spiketrains.

    Only counts run 0

    :param ~neo.core.Block neo: Neo Object which has spikes in it
    :return: The number of spikes in the first segment
    """
    return count_spiketrains(neo.segments[0].spiketrains)
