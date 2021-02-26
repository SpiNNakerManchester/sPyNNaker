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


def calculate_stdp_times(pre_spikes, post_spikes, plastic_delay):
    # If no post spikes, no changes
    if len(post_spikes) == 0:
        return numpy.zeros(0), numpy.zeros(0)

    # Get the spikes and time differences that will be considered by
    # the simulation (as the last pre-spike will be considered differently)
    last_pre_spike_delayed = pre_spikes[-1] - plastic_delay
    considered_post_spikes = post_spikes[post_spikes < last_pre_spike_delayed]
    if len(considered_post_spikes) == 0:
        return numpy.zeros(0), numpy.zeros(0)
    potentiation_time_diff = numpy.ravel(numpy.subtract.outer(
        considered_post_spikes + plastic_delay, pre_spikes[:-1]))
    potentiation_times = (
        potentiation_time_diff[potentiation_time_diff > 0] * -1)
    depression_time_diff = numpy.ravel(numpy.subtract.outer(
        considered_post_spikes + plastic_delay, pre_spikes))
    depression_times = depression_time_diff[depression_time_diff < 0]
    return potentiation_times, depression_times


def calculate_spike_pair_additive_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, max_weight,
        a_plus, a_minus, tau_plus, tau_minus):
    """ Calculates the expected stdp weight for SpikePair Additive STDP

    :param pre_spikes:
    :param post_spikes:
    :param initial_weight:
    :param plastic_delay:
    :param max_weight:
    :param a_plus:
    :param a_minus:
    :param tau_plus:
    :param tau_minus:
    :return:
    """
    potentiation_times, depression_times = calculate_stdp_times(
        pre_spikes, post_spikes, plastic_delay)

    # Work out the weight according to the additive rule
    potentiations = max_weight * a_plus * numpy.exp(
        (potentiation_times / tau_plus))
    depressions = max_weight * a_minus * numpy.exp(
        (depression_times / tau_minus))
    return initial_weight + numpy.sum(potentiations) - numpy.sum(depressions)


def calculate_spike_pair_multiplicative_stdp_weight(
        pre_spikes, post_spikes, initial_weight, plastic_delay, min_weight,
        max_weight, a_plus, a_minus, tau_plus, tau_minus):
    """
    Calculates the expected stdp weight for SpikePair Multiplicative STDP

    :param iterable(int) pre_spikes: Spikes going into the model
    :param iterable(int) post_spikes: Spikes recorded on the model
    :param float initial_weight: Starting weight for the model
    :param int plastic_delay: param of the stdp model
    :param float min_weight: param of the stdp model
    :param float max_weight: param of the stdp model
    :param float a_plus: param of the stdp model
    :param float a_minus: param of the stdp model
    :param float tau_plus: param of the stdp model
    :param float tau_minus: param of the stdp model
    :return:
    """
    potentiation_times, depression_times = calculate_stdp_times(
        pre_spikes, post_spikes, plastic_delay)

    # Work out the weight according to the multiplicative rule
    potentiations = (max_weight - initial_weight) * a_plus * numpy.exp(
        (potentiation_times / tau_plus))
    depressions = (initial_weight - min_weight) * a_minus * numpy.exp(
        (depression_times / tau_minus))
    return initial_weight + numpy.sum(potentiations) - numpy.sum(depressions)
