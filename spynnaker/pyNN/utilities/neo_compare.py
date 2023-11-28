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

from neo import AnalogSignal, Block, Segment, SpikeTrain
from typing import List


def compare_spiketrain(
        spiketrain1: SpikeTrain, spiketrain2: SpikeTrain, *, same_length=True):
    """
    Checks two spike trains have the exact same data.

    :param ~neo.core.SpikeTrain spiketrain1: first spike train
    :param ~neo.core.SpikeTrain spiketrain2: second spike train
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional spikes after the first ends. This is used to
        compare data extracted part way with data extracted at the end.
    :raises AssertionError: If the spike trains are not equal
    """
    id1 = spiketrain1.annotations['source_index']
    id2 = spiketrain2.annotations['source_index']
    if id1 != id2:
        raise AssertionError(
            f"Different annotations['source_index'] found {id1} and {id2}")
    if same_length and len(spiketrain1) != len(spiketrain2):
        raise AssertionError(
            f"spiketrains1 has {len(spiketrain1)} spikes while spiketrains2 "
            f"has {len(spiketrain2)} for ID {id1}")
    for spike1, spike2 in zip(spiketrain1, spiketrain2):
        if spike1 != spike2:
            # print(id1, spiketrain1, spiketrain2)
            raise AssertionError(
                f"spike1 is {spike1} while spike2 is {spike2} for ID {id1}")


def compare_spiketrains(
        spiketrains1: List[SpikeTrain], spiketrains2: List[SpikeTrain], *,
        same_data=True, same_length=True):
    """
    Check two Lists of spike trains have the exact same data.

    :param list(~neo.core.SpikeTrain) spiketrains1:
        First list of spike trains to compare
    :param list(~neo.core.SpikeTrain) spiketrains2:
        Second list of spike trains to compare
    :param bool same_data: Flag to indicate if the same type of data is held,
        i.e., same spikes, v, gsyn_exc and gsyn_inh.
        If False allows one or both lists to be Empty.
        Even if False none empty lists must be the same length
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional spikes after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the spike trains are not equal
    """
    if not same_data and (not spiketrains1 or not spiketrains2):
        return
    if len(spiketrains1) != len(spiketrains2):
        raise AssertionError(
            f"spiketrains1 has {len(spiketrains1)} spiketrains while "
            f"spiketrains2 fas {len(spiketrains2)} analogsignalarrays")
    for spiketrain1, spiketrain2 in zip(spiketrains1, spiketrains2):
        compare_spiketrain(spiketrain1, spiketrain2, same_length=same_length)


def compare_analogsignal(
        as1: AnalogSignal, as2: AnalogSignal, *, same_length=True):
    """
    Compares two analog signal objects to see if they are the same.

    :param ~neo.core.AnalogSignal as1:
        first analog signal holding list of individual analog signal objects
    :param ~neo.core.AnalogSignal as2:
        second analog signal holding list of individual analog signal objects
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional data after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the analog signals are not equal
    """
    as1_index = as1.annotations["channel_names"]
    as2_index = as2.annotations["channel_names"]

    if as1.name != as2.name:
        raise AssertionError(
            f"analogsignalarray1 has name {as1.name} while "
            f"analogsignalarray1 has {as2.name}")

    if same_length and len(as1_index) != len(as2_index):
        raise AssertionError(
            f"channel_index 1 has len {len(as1_index)} while "
            f"channel_index 2 has {len(as2_index)} for {as1.name}")

    for id1, id2 in zip(as1_index, as2_index):
        if id1 != id2:
            raise AssertionError(
                f"ID 1 is {id1} while ID 2 is {id2} for {as1.name}")

    if same_length and len(as1.times) != len(as2.times):
        raise AssertionError(
            f"times 1 has len {len(as1.times)} while "
            f"times 2 has {len(as2.times)} for {as1.name}")

    for time1, time2 in zip(as1.times, as2.times):
        if time1 != time2:
            raise AssertionError(
                f"time 1 is {time1} while time 2 is {time2} for {as1.name}")

    if same_length and len(as1) != len(as2):
        raise AssertionError(
            f"analogsignal 1 has len {len(as1)} while "
            f"analogsignal 2 has {len(as2)} for {as1.name}")

    for signal1, signal2 in zip(as1, as2):
        # print(signal1, signal2)
        if len(signal1) != len(signal2):
            raise AssertionError(
                f"signal 1 has len {len(signal1)} while "
                f"signal 2 has {len(signal2)} for {as1.name}")
        for value1, value2 in zip(signal1, signal2):
            if value1 != value2:
                raise AssertionError(
                    f"value 1 is {value1} while "
                    f"value 2 is {value1} for {as1.name}")


def compare_segments(
        seg1: Segment, seg2: Segment, *, same_data=True, same_length=True):
    """
    :param ~neo.core.Segment seg1: First Segment to check
    :param ~neo.core.Segment seg2: Second Segment to check
    :param bool same_data: Flag to indicate if the same type of data is held,
        i.e., same spikes, v, gsyn_exc and gsyn_inh.
        If False only data in both blocks is compared
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional data after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the segments are not equal
    """
    compare_spiketrains(
        seg1.spiketrains, seg2.spiketrains,
        same_data=same_data, same_length=same_length)
    seg1_analogsignals = seg1.analogsignals
    seg2_analogsignals = seg2.analogsignals

    if same_data and len(seg1_analogsignals) != len(seg2_analogsignals):
        raise AssertionError(
            f"Segment1 has {len(seg1_analogsignals)} analogsignalarrays while "
            f"Segment2 has {len(seg1_analogsignals)} analogsignalarrays")

    for analogsignal1 in seg1_analogsignals:
        name = analogsignal1.name
        filtered = seg2.filter(name=name)
        if (not filtered) and same_data:
            raise AssertionError(
                f"Segment1 has {name} data while Segment2 does not")
        analogsignal2 = seg2.filter(name=name)[0]
        compare_analogsignal(analogsignal1, analogsignal2,
                             same_length=same_length)


def compare_blocks(
        neo1: Block, neo2: Block, *,
        same_runs=True, same_data=True, same_length=True):
    """
    Compares two neo Blocks to see if they hold the same data.

    :param ~neo.core.Block neo1: First block to check
    :param ~neo.core.Block neo2: Second block to check
    :param bool same_runs: Flag to signal if blocks are the same length.
        If False extra segments in the larger block are ignored
    :param bool same_data: Flag to indicate if the same type of data is held,
        i.e., same spikes, v, gsyn_exc and gsyn_inh.
        If False only data in both blocks is compared
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional data after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the blocks are not equal
    """
    if same_runs and len(neo1.segments) != len(neo2.segments):
        raise AssertionError(
            f"Block1 has {len(neo1.segments)} segments while "
            f"block2 has {len(neo2.segments)} segments")
    for seg1, seg2 in zip(neo1.segments, neo2.segments):
        compare_segments(seg1, seg2,
                         same_data=same_data, same_length=same_length)
