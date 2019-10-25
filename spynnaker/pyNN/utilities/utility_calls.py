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

"""
utility class containing simple helper methods
"""
from decimal import Decimal
import os
import logging
import math
import numpy
from scipy.stats import binom
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException

MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

logger = logging.getLogger(__name__)


def check_directory_exists_and_create_if_not(filename):
    """ Create a parent directory for a file if it doesn't exist

    :param filename: The file whose parent directory is to be created
    """
    directory = os.path.dirname(filename)
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)


def convert_param_to_numpy(param, no_atoms):
    """ Convert parameters into numpy arrays

    :param param: the param to convert
    :param no_atoms: the number of atoms available for conversion of param
    :return numpy.array: the converted param in whatever format it was given
    """

    # Deal with random distributions by generating values
    if globals_variables.get_simulator().is_a_pynn_random(param):

        # numpy reduces a single valued array to a single value, so enforce
        # that it is an array
        param_value = param.next(n=no_atoms)
        if hasattr(param_value, '__iter__'):
            return numpy.array(param_value, dtype="float")
        return numpy.array([param_value], dtype="float")

    # Deal with a single value by exploding to multiple values
    if not hasattr(param, '__iter__'):
        return numpy.array([param] * no_atoms, dtype="float")

    # Deal with multiple values, but not the correct number of them
    if len(param) != no_atoms:
        raise ConfigurationException(
            "The number of params does not equal with the number of atoms in"
            " the vertex")

    # Deal with the correct number of multiple values
    return numpy.array(param, dtype="float")


def convert_to(value, data_type):
    """ Convert a value to a given data type

    :param value: The value to convert
    :param data_type: The data type to convert to
    :return: The converted data as a numpy data type
    """
    return numpy.round(
        float(Decimal(str(value)) * data_type.scale)).astype(
            numpy.dtype(data_type.struct_encoding))


def read_in_data_from_file(
        file_path, min_atom, max_atom, min_time, max_time, extra=False):
    """ Read in a file of data values where the values are in a format of:
        <time>\t<atom ID>\t<data value>

    :param file_path: absolute path to a file containing the data
    :param min_atom: min neuron ID to which neurons to read in
    :param max_atom: max neuron ID to which neurons to read in
    :param min_time: min time slot to read neurons values of.
    :param max_time: max time slot to read neurons values of.
    :return: a numpy array of (time stamp, atom ID, data value)
    """
    times = list()
    atom_ids = list()
    data_items = list()
    evaluator = SafeEval()
    with open(file_path, 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if extra:
                time, neuron_id, data_value, extra = line.split("\t")
            else:
                time, neuron_id, data_value = line.split("\t")
            time = float(evaluator.eval(time))
            neuron_id = int(evaluator.eval(neuron_id))
            data_value = float(evaluator.eval(data_value))
            if (min_atom <= neuron_id < max_atom and
                    min_time <= time < max_time):
                times.append(time)
                atom_ids.append(neuron_id)
                data_items.append(data_value)
            else:
                print("failed to enter {}:{}".format(neuron_id, time))

    result = numpy.dstack((atom_ids, times, data_items))[0]
    return result[numpy.lexsort((times, atom_ids))]


def read_spikes_from_file(file_path, min_atom=0, max_atom=float('inf'),
                          min_time=0, max_time=float('inf'), split_value="\t"):
    """ Read spikes from a file formatted as:\
        <time>\t<neuron ID>

    :param file_path: absolute path to a file containing spike values
    :type file_path: str
    :param min_atom: min neuron ID to which neurons to read in
    :type min_atom: int
    :param max_atom: max neuron ID to which neurons to read in
    :type max_atom: int
    :param min_time: min time slot to read neurons values of.
    :type min_time: int
    :param max_time: max time slot to read neurons values of.
    :type max_time: int
    :param split_value: the pattern to split by
    :type split_value: str
    :return:\
        a numpy array with max_atom elements each of which is a list of\
        spike times.
    :rtype: numpy.array(int, int)
    """
    # pylint: disable=too-many-arguments

    # For backward compatibility as previous version tested for None rather
    # than having default values
    if min_atom is None:
        min_atom = 0
    if max_atom is None:
        max_atom = float('inf')
    if min_time is None:
        min_time = 0
    if max_time is None:
        max_time = float('inf')

    data = []
    with open(file_path, 'r') as fsource:
        read_data = fsource.readlines()

    evaluator = SafeEval()
    for line in read_data:
        if line.startswith('#'):
            continue
        values = line.split(split_value)
        time = float(evaluator.eval(values[0]))
        neuron_id = float(evaluator.eval(values[1]))
        if (min_atom <= neuron_id < max_atom and
                min_time <= time < max_time):
            data.append([neuron_id, time])
    data.sort()
    return numpy.array(data)


def get_probable_maximum_selected(
        n_total_trials, n_trials, selection_prob, chance=(1.0 / 100.0)):
    """ Get the likely maximum number of items that will be selected from a\
        set of n_trials from a total set of n_total_trials\
        with a probability of selection of selection_prob
    """
    prob = 1.0 - (chance / float(n_total_trials))
    return binom.ppf(prob, n_trials, selection_prob)


def get_probability_within_range(dist, lower, upper):
    """ Get the probability that a value will fall within the given range for\
        a given RandomDistribution
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return (stats.cdf(dist, upper) - stats.cdf(dist, lower))


def get_maximum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely maximum value of a RandomDistribution given a\
        number of draws
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    prob = 1.0 - (chance / float(n_items))
    return stats.ppf(dist, prob)


def get_minimum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely minimum value of a RandomDistribution given a\
        number of draws
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    prob = chance / float(n_items)
    return stats.ppf(dist, prob)


def get_mean(dist):
    """ Get the mean of a RandomDistribution
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return stats.mean(dist)


def get_standard_deviation(dist):
    """ Get the standard deviation of a RandomDistribution
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return stats.std(dist)


def get_variance(dist):
    """ Get the variance of a RandomDistribution
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return stats.var(dist)


def high(dist):
    """ Gets the high or max boundary value for this distribution

    Could return None
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return stats.high(dist)


def low(dist):
    """ Gets the high or min boundary value for this distribution

    Could return None
    """
    simulator = globals_variables.get_simulator()
    stats = simulator.get_distribution_to_stats()[dist.name]
    return stats.low(dist)


def validate_mars_kiss_64_seed(seed):
    """ Update the seed to make it compatible with the rng algorithm
    """
    if seed[1] == 0:
        # y (<- seed[1]) can't be zero so set to arbitrary non-zero if so
        seed[1] = 13031301

    # avoid z=c=0 and make < 698769069
    seed[3] = seed[3] % 698769068 + 1
    return seed


def check_sampling_interval(sampling_interval):
    step = globals_variables.get_simulator().machine_time_step / 1000
    if sampling_interval is None:
        return step
    rate = int(sampling_interval / step)
    if sampling_interval != rate * step:
        msg = "sampling_interval {} is not an an integer " \
              "multiple of the simulation timestep {}" \
              "".format(sampling_interval, step)
        raise ConfigurationException(msg)
    if rate > MAX_RATE:
        msg = "sampling_interval {} higher than max allowed which is {}" \
              "".format(sampling_interval, step * MAX_RATE)
        raise ConfigurationException(msg)
    return sampling_interval


def get_n_bits(n_values):
    """ Determine how many bits are required for the given number of values
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log(n_values, 2)))
