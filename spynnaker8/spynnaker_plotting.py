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

import spynnaker.spynnaker_plotting as new_plotting
from spynnaker.spynnaker_plotting import SpynnakerPanel as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


def plot_spiketrains(axes, spiketrains, label='', **options):
    """
    Plot all spike trains in a Segment in a raster plot.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes axes: An Axes in a matplotlib figure
    :param list(~neo.core.SpikeTrain) spiketrains: List of spike times
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.plot_spiketrains(axes, spiketrains, label, **options)


def plot_spikes_numpy(axes, spikes, label='', **options):
    """
    Plot all spikes.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes axes: An Axes in a matplotlib figure
    :param ~numpy.ndarray spikes: spynakker7 format numpy array of spikes
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.plot_spikes_numpy(axes, spikes, label, **options)


def heat_plot_numpy(axes, data, label='', **options):
    """
    Plots neurons, times and values into a heatmap.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes axes: An Axes in a matplotlib figure
    :param ~numpy.ndarray data: numpy array of values in spynnaker7 format
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.heat_plot_numpy(axes, data, label, **options)


def heat_plot_neo(axes, signal_array, label='', **options):
    """
    Plots neurons, times and values into a heatmap.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes axes: An Axes in a matplotlib figure
    :param ~neo.core.AnalogSignal signal_array: Neo Signal array Object
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.heat_plot_neo(axes, signal_array, label, **options)


def plot_segment(axes, segment, label='', **options):
    """
    Plots a segment into a plot of spikes or a heatmap.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes axes: An Axes in a matplotlib figure
    :param ~neo.core.Segment segment: Data for one run to plot
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.plot_segment(axes, segment, label, **options)


class SpynnakerPanel(_BaseClass):
    """
    Represents a single panel in a multi-panel figure.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.
    """
    def __init__(self, *data, **options):
        moved_in_v6(
            "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
        super().__init__(*data, **options)
