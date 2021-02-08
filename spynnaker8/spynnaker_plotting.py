# Copyright (c) 2021 The University of Manchester
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

import spynnaker.spynnaker_plotting as new_plotting
from spynnaker.spynnaker_plotting import SpynnakerPanel as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


def plot_spiketrains(ax, spiketrains, label='', **options):
    """ Plot all spike trains in a Segment in a raster plot.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes ax: An Axes in a matplotlib figure
    :param list(~neo.core.SpikeTrain) spiketrains: List of spiketimes
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.plot_spiketrains(ax, spiketrains, label, **options)


def plot_spikes_numpy(ax, spikes, label='', **options):
    """ Plot all spikes

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes ax: An Axes in a matplotlib figure
    :param ~numpy.ndarray spikes: spynakker7 format nparray of spikes
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.plot_spikes_numpy(ax, spikes, label, **options)


def heat_plot_numpy(ax, data, label='', **options):
    """ Plots neurons, times and values into a heatmap

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes ax: An Axes in a matplotlib figure
    :param ~numpy.ndarray data: nparray of values in spynnaker7 format
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.heat_plot_numpy(ax, data, label, **options)


def heat_plot_neo(ax, signal_array, label='', **options):
    """ Plots neurons, times and values into a heatmap

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.

    :param ~matplotlib.axes.Axes ax: An Axes in a matplotlib figure
    :param ~neo.core.AnalogSignal signal_array: Neo Signal array Object
    :param str label: Label for the graph
    :param options: plotting options
    """
    moved_in_v6(
        "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
    new_plotting.heat_plot_neo(ax, signal_array, label, **options)


def plot_segment(axes, segment, label='', **options):
    """ Plots a segment into a plot of spikes or a heatmap

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
    """ Represents a single panel in a multi-panel figure.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.spynnaker_plotting` instead.
    """
    def __init__(self, *data, **options):
        moved_in_v6(
            "spynnaker8.spynnaker_plotting", "spynnaker.spynnaker_plotting")
        super(SpynnakerPanel, self).__init__(*data, **options)
