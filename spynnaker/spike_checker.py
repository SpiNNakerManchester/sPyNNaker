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
                raise Exception("Unexpected spike at time " + str(row[1]))
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
            raise Exception("Unexpected spike at time " + str(row[1]))
    if False in used:
        numpy.savetxt("sorted_spikes.csv", sorted_spikes, fmt=['%d', '%d'],
                      delimiter=',')
        print(used)
        raise Exception("Expected " + str(lines) + " spike lines")


if __name__ == '__main__':
    _spikes = numpy.loadtxt("sorted_spikes.csv", delimiter=',')
    synfire_multiple_lines_spike_checker(_spikes, 200, 10, wrap_around=False)
    # synfire_spike_checker(_spikes, 20)
