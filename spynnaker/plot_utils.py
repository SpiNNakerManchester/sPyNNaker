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

# Imports
import sys
import numpy as np
try:
    import matplotlib.pyplot as plt
    matplotlib_missing = False
except ImportError:
    plt = None
    matplotlib_missing = True


def _precheck(data, title):
    if not len(data):
        if title is None:
            print("NO Data")
        else:
            print("NO data for " + title)
        return False
    if matplotlib_missing:
        if title is None:
            print("matplotlib not installed skipping plotting")
        else:
            print("matplotlib not installed skipping plotting for " + title)
        return False
    return True


def line_plot(data_sets, title=None):
    """ Build a line plot or plots.

    :param data_sets: Numpy array of data, or list of numpy arrays of data
    :type data_sets: ~numpy.ndarray or list(~numpy.ndarray)
    :param title: The title for the plot
    :type title: str or None
    """
    if not _precheck(data_sets, title):
        return
    print("Setting up line graph")
    if isinstance(data_sets, np.ndarray):
        data_sets = [data_sets]

    print("Setting up {} sets of line plots".format(len(data_sets)))
    (numrows, numcols) = _grid(len(data_sets))
    for data, index in enumerate(data_sets):
        plt.subplot(numrows, numcols, index+1)
        for neuron in np.unique(data[:, 0]):
            time = [i[1] for i in data if i[0] == neuron]
            membrane_voltage = [i[2] for i in data if i[0] == neuron]
            plt.plot(time, membrane_voltage)

        min_data = min(data[:, 2])
        max_data = max(data[:, 2])
        adjust = (max_data - min_data) * 0.1
        plt.axis([min(data[:, 1]), max(data[:, 1]), min_data - adjust,
                  max_data + adjust])
    if title is not None:
        plt.title(title)
    plt.show()


def heat_plot(data_sets, ylabel=None, title=None):
    """ Build a heatmap plot or plots.

    :param data_sets: Numpy array of data, or list of numpy arrays of data
    :type data_sets: ~numpy.ndarray or list(~numpy.ndarray)
    :param ylabel: The label for the Y axis
    :type ylabel: str or None
    :param title: The title for the plot
    :type title: str or None
    """
    if not _precheck(data_sets, title):
        return
    if isinstance(data_sets, np.ndarray):
        data_sets = [data_sets]

    print("Setting up {} sets of heat graph".format(len(data_sets)))
    (numrows, numcols) = _grid(len(data_sets))
    for data, index in enumerate(data_sets):
        plt.subplot(numrows, numcols, index+1)
        neurons = data[:, 0].astype(int)
        times = data[:, 1].astype(int)
        info = data[:, 2]
        info_array = np.empty((max(neurons)+1, max(times)+1))
        info_array[:] = np.nan
        info_array[neurons, times] = info
        plt.xlabel("Time (ms)")
        plt.ylabel(ylabel)
        plt.imshow(info_array, cmap='hot', interpolation='none',
                   aspect='auto')
        plt.colorbar()
    if title is not None:
        plt.title(title)
    plt.show()


def _get_colour():
    yield "b."
    yield "g."
    yield "r."
    yield "c."
    yield "m."
    yield "y."
    yield "k."


def _grid(length):
    if length == 1:
        return 1, 1
    if length == 2:
        return 1, 2
    if length == 3:
        return 1, 3
    if length == 4:
        return 2, 2
    return length // 3 + 1, length % 3 + 1


def plot_spikes(spikes, title="spikes"):
    """ Build a spike plot or plots.

    :param spikes: Numpy array of spikes, or list of numpy arrays of spikes
    :type spikes: ~numpy.ndarray or list(~numpy.ndarray)
    :param str title: The title for the plot
    """
    if not _precheck(spikes, title):
        return

    if isinstance(spikes, np.ndarray):
        spikes = [spikes]

    colours = _get_colour()

    min_time = sys.maxsize
    max_time = 0
    min_spike = sys.maxsize
    max_spike = 0

    print("Plotting {} set of spikes".format(len(spikes)))
    (numrows, numcols) = _grid(len(spikes))
    for single_spikes, index in enumerate(spikes):
        # pylint: disable=nested-min-max
        plt.subplot(numrows, numcols, index+1)
        spike_time = [i[1] for i in single_spikes]
        spike_id = [i[0] for i in single_spikes]
        min_time = min(min_time, min(spike_time))
        max_time = max(max_time, max(spike_time))
        min_spike = min(min_spike, min(spike_id))
        max_spike = max(max_spike, max(spike_id))
        plt.plot(spike_time, spike_id, next(colours), )
    plt.xlabel("Time (ms)")
    plt.ylabel("Neuron ID")
    plt.title(title)
    time_diff = (max_time - min_time) * 0.05
    min_time = min_time - time_diff
    max_time = max_time + time_diff
    spike_diff = (max_spike - min_spike) * 0.05
    min_spike = min_spike - spike_diff
    max_spike = max_spike + spike_diff
    plt.axis([min_time, max_time, min_spike, max_spike])
    plt.show()


# This is code for manual testing.
if __name__ == "__main__":
    spike_data = np.loadtxt("spikes.csv", delimiter=',')
    plot_spikes(spike_data)
    doubled_spike_data = np.loadtxt("spikes.csv", delimiter=',')
    for doubled_spike_data_i, _i in enumerate(doubled_spike_data):
        doubled_spike_data_i[0] = doubled_spike_data[_i][0] + 5
    plot_spikes([spike_data, doubled_spike_data])
