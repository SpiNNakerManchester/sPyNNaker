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

# from __future__ import print_function


def compare_spiketrain(spiketrain1, spiketrain2, same_length=True):
    """ Checks two Spiketrains have the exact same data

    :param ~neo.core.SpikeTrain spiketrain1: first spiketrain
    :param ~neo.core.SpikeTrain spiketrain2: second spiketrain
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional spikes after the first ends. This is used to
        compare data extracted part way with data extracted at the end.
    :rtype: None
    :raises AssertionError: If the spiketrains are not equal
    """
    id1 = spiketrain1.annotations['source_index']
    id2 = spiketrain2.annotations['source_index']
    if id1 != id2:
        raise AssertionError(
            "Different annotations['source_index'] found {} and {}".format(
                id1, id2))
    if same_length and len(spiketrain1) != len(spiketrain2):
        raise AssertionError(
            "spiketrains1 has {} spikes while spiketrains2 as {} for ID {}"
            .format(len(spiketrain1), len(spiketrain2), id1))
    for spike1, spike2 in zip(spiketrain1, spiketrain2):
        if spike1 != spike2:
            # print(id1, spiketrain1, spiketrain2)
            raise AssertionError(
                "spike1 is {} while spike2 is {} for ID {}".format(
                    spike1, spike2, id1))


def compare_spiketrains(
        spiketrains1, spiketrains2, same_data=True, same_length=True):
    """ Check two Lists of SpikeTrains have the exact same data

    :param list(~neo.core.SpikeTrain) spiketrains1:
        First list SpikeTrains to compare
    :param list(~neo.core.SpikeTrain) spiketrains2:
        Second list of SpikeTrains to compare
    :param bool same_data: Flag to indicate if the same type of data is held,
        i.e., same spikes, v, gsyn_exc and gsyn_inh.
        If False allows one or both lists to be Empty.
        Even if False none empty lists must be the same length
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional spikes after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the spiketrains are not equal
    """
    if not same_data and (not spiketrains1 or not spiketrains2):
        return
    if len(spiketrains1) != len(spiketrains2):
        raise AssertionError(
            "spiketrains1 has {} spiketrains while spiketrains2 as {} "
            "analogsignalarrays".format(
                len(spiketrains1), len(spiketrains2)))
    for spiketrain1, spiketrain2 in zip(spiketrains1, spiketrains2):
        compare_spiketrain(spiketrain1, spiketrain2, same_length)


def compare_analogsignal(as1, as2, same_length=True):
    """ Compares two analogsignal Objects to see if they are the same

    :param ~neo.core.AnalogSignal as1:
        first analogsignal holding list of individual analogsignal Objects
    :param ~neo.core.AnalogSignal as2:
        second analogsignal holding list of individual analogsignal Objects
    :param bool same_length: Flag to indicate if the same length of data is
        held, i.e., all spikes up to the same time. If False allows one trains
        to have additional data after the first ends. This is used to compare
        data extracted part way with data extracted at the end.
    :raises AssertionError: If the analogsignals are not equal
    """
    as1_index = as1.channel_index.index
    as2_index = as2.channel_index.index

    if as1.name != as2.name:
        raise AssertionError(
            "analogsignalarray1 has name {} while analogsignalarray1 has {}"
            .format(as1.name, as2.name))

    if same_length and len(as1_index) != len(as2_index):
        raise AssertionError(
            "channel_index 1 has len {} while channel_index 2 has {} for {}"
            .format(len(as1_index), len(as2_index), as1.name))

    for id1, id2 in zip(as1_index, as2_index):
        if id1 != id2:
            raise AssertionError(
                "ID 1 is {} while ID 2 is {} for {}".format(
                    id1, id2, as1.name))

    if same_length and len(as1.times) != len(as2.times):
        raise AssertionError(
            "times 1 has len {} while times 2 has {} for {}".format(
                len(as1.times), len(as2.times), as1.name))

    for time1, time2 in zip(as1.times, as2.times):
        if time1 != time2:
            raise AssertionError(
                "time 1 is {} while time 2 is {} for {}".format(
                    time1, time2, as1.name))

    if same_length and len(as1) != len(as2):
        raise AssertionError(
            "analogsignal 1 has len {} while analogsignal 2 has {} for {}"
            .format(len(as1), len(as2), as1.name))

    for signal1, signal2 in zip(as1, as2):
        # print(signal1, signal2)
        if len(signal1) != len(signal2):
            raise AssertionError(
                "signal 1 has len {} while signal 2 has {} for {}".format(
                    len(signal1), len(signal2), as1.name))
        for value1, value2 in zip(signal1, signal2):
            if value1 != value2:
                raise AssertionError(
                    "value 1 is {} while value2 is {} for {}".format(
                        value1, value2, as1.name))


def compare_segments(seg1, seg2, same_data=True, same_length=True):
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
        seg1.spiketrains, seg2.spiketrains, same_data, same_length)
    seg1_analogsignals = seg1.analogsignals
    seg2_analogsignals = seg2.analogsignals

    if same_data and len(seg1_analogsignals) != len(seg2_analogsignals):
        raise AssertionError(
            "Segment1 has {} analogsignalarrays while Segment2 as {} "
            "analogsignalarrays".format(
                len(seg1_analogsignals), len(seg1_analogsignals)))

    for analogsignal1 in seg1_analogsignals:
        name = analogsignal1.name
        filtered = seg2.filter(name=name)
        if not filtered:
            if same_data:
                raise AssertionError(
                    "Segment1 has {} data while Segment2 does not".format(
                        name))
        else:
            analogsignal2 = seg2.filter(name=name)[0]
            compare_analogsignal(analogsignal1, analogsignal2, same_length)


def compare_blocks(
        neo1, neo2, same_runs=True, same_data=True, same_length=True):
    """ Compares two neo Blocks to see if they hold the same data.

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
            "Block1 has {} segments while block2 as {} segments".format(
                len(neo1.segments), len(neo2.segments)))
    for seg1, seg2 in zip(neo1.segments, neo2.segments):
        compare_segments(seg1, seg2, same_data, same_length)
