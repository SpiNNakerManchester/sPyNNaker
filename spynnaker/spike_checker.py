# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy


def synfire_spike_checker(spikes, nNeurons):
    """
    :param spikes: The spike data to check.
    :type spikes: ~numpy.ndarray or list(~numpy.ndarray)
    :param int nNeurons: The number of neurons.
    :raises Exception: If there is a problem with the data
    """
    if isinstance(spikes, numpy.ndarray):
        sorted_spikes = spikes[spikes[:, 1].argsort()]
        print(len(sorted_spikes))
        num = 0
        for row in sorted_spikes:
            if num != round(row[0]):
                numpy.savetxt("spikes.csv", sorted_spikes, fmt=['%d', '%d'],
                              delimiter=',')
                raise ValueError(f"Unexpected spike at time {row[1]}")
            num += 1
            if num >= nNeurons:
                num = 0
    else:
        for single in spikes:
            synfire_spike_checker(single, nNeurons)


def synfire_multiple_lines_spike_checker(
        spikes, nNeurons, lines, wrap_around=True):
    """
    Checks that there are the expected number of spike lines

    :param spikes: The spikes
    :type spikes: ~numpy.ndarray or list(~numpy.ndarray)
    :param int nNeurons: The number of neurons.
    :param int lines: Expected number of lines
    :param bool wrap_around:
        If True the lines will wrap around when reaching the last neuron.
    :raises Exception: If there is a problem with the data
    """
    sorted_spikes = spikes[spikes[:, 1].argsort()]
    nums = [0] * lines
    used = [False] * lines
    for row in sorted_spikes:
        node = round(row[0])
        found = False
        for i in range(lines):
            if nums[i] == node:
                found = True
                nums[i] += 1
                if nums[i] >= nNeurons and wrap_around:
                    nums[i] = 0
                used[i] = True
                break
        if not found:
            numpy.savetxt("sorted_spikes.csv", sorted_spikes, fmt=['%d', '%d'],
                          delimiter=',')
            raise ValueError(f"Unexpected spike at time {row[1]}")
    if False in used:
        numpy.savetxt("sorted_spikes.csv", sorted_spikes, fmt=['%d', '%d'],
                      delimiter=',')
        print(used)
        raise ValueError(f"Expected {lines} spike lines")


if __name__ == '__main__':
    _spikes = numpy.loadtxt("sorted_spikes.csv", delimiter=',')
    synfire_multiple_lines_spike_checker(_spikes, 200, 10, wrap_around=False)
    # synfire_spike_checker(_spikes, 20)
