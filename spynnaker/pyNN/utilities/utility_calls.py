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
import logging
import os
import math
import numpy
from math import isnan
from pyNN.random import RandomDistribution
from scipy.stats import binom
from spinn_utilities.log import FormatAdapter
from spinn_utilities.safe_eval import SafeEval
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from spynnaker.pyNN.utilities.random_stats import (
    RandomStatsExponentialImpl, RandomStatsGammaImpl, RandomStatsLogNormalImpl,
    RandomStatsNormalClippedImpl, RandomStatsNormalImpl,
    RandomStatsPoissonImpl, RandomStatsRandIntImpl, RandomStatsUniformImpl,
    RandomStatsVonmisesImpl, RandomStatsBinomialImpl)
from spinn_front_end_common.utilities.constants import (
    MICRO_TO_SECOND_CONVERSION)
from spynnaker.pyNN.utilities.constants import WRITE_BANDWIDTH_BYTES_PER_SECOND

logger = FormatAdapter(logging.getLogger(__name__))

MAX_RATE = 2 ** 32 - 1  # To allow a unit32_t to be used to store the rate

BASE_RANDOM_FOR_MARS_64 = 0x80000000
CAP_RANDOM_FOR_MARS_64 = 0x7FFFFFFF
# in order are x, y, z, c
N_RANDOM_NUMBERS = 4
ARBITRARY_Y = 13031301
MARS_C_MAX = 698769068

STATS_BY_NAME = {
    'binomial': RandomStatsBinomialImpl(),
    'gamma': RandomStatsGammaImpl(),
    'exponential': RandomStatsExponentialImpl(),
    'lognormal': RandomStatsLogNormalImpl(),
    'normal': RandomStatsNormalImpl(),
    'normal_clipped': RandomStatsNormalClippedImpl(),
    'normal_clipped_to_boundary': RandomStatsNormalClippedImpl(),
    'poisson': RandomStatsPoissonImpl(),
    'uniform': RandomStatsUniformImpl(),
    'randint': RandomStatsRandIntImpl(),
    'vonmises': RandomStatsVonmisesImpl()}


def check_directory_exists_and_create_if_not(filename):
    """ Create a parent directory for a file if it doesn't exist

    :param str filename: The file whose parent directory is to be created
    """
    directory = os.path.dirname(filename)
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)


def convert_param_to_numpy(param, no_atoms):
    """ Convert parameters into numpy arrays.

    :param param: the param to convert
    :type param: ~pyNN.random.NumpyRNG or int or float or list(int) or
        list(float) or ~numpy.ndarray
    :param int no_atoms: the number of atoms available for conversion of param
    :return: the converted param as an array of floats
    :rtype: ~numpy.ndarray(float)
    """

    # Deal with random distributions by generating values
    if isinstance(param, RandomDistribution):

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
    :param ~data_specification.enums.DataType data_type:
        The data type to convert to
    :return: The converted data as a numpy data type
    :rtype: ~numpy.ndarray(int32)
    """
    return numpy.round(data_type.encode_as_int(value)).astype(
        data_type.struct_encoding)


def read_in_data_from_file(
        file_path, min_atom, max_atom, min_time, max_time, extra=False):
    """ Read in a file of data values where the values are in a format of:
        <time>\t<atom ID>\t<data value>

    :param str file_path: absolute path to a file containing the data
    :param int min_atom: min neuron ID to which neurons to read in
    :param int max_atom: max neuron ID to which neurons to read in
    :param extra:
    :param min_time: min time slot to read neurons values of.
    :type min_time: float or int
    :param max_time: max time slot to read neurons values of.
    :type max_time: float or int
    :return: a numpy array of (time stamp, atom ID, data value)
    :rtype: ~numpy.ndarray(tuple(float, int, float))
    """
    times = list()
    atom_ids = list()
    data_items = list()
    evaluator = SafeEval()
    with open(file_path, 'r', encoding="utf-8") as f:
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
    """ Read spikes from a file formatted as:
        <time>\t<neuron ID>

    :param str file_path: absolute path to a file containing spike values
    :param min_atom: min neuron ID to which neurons to read in
    :type min_atom: int or float
    :param max_atom: max neuron ID to which neurons to read in
    :type max_atom: int or float
    :param min_time: min time slot to read neurons values of.
    :type min_time: float or int
    :param max_time: max time slot to read neurons values of.
    :type max_time: float or int
    :param str split_value: the pattern to split by
    :return:
        a numpy array with max_atom elements each of which is a list of\
        spike times.
    :rtype: numpy.ndarray(int, int)
    """
    # pylint: disable=too-many-arguments

    # For backward compatibility as previous version tested for None rather
    # than having default values
    if min_atom is None:
        min_atom = 0.0
    if max_atom is None:
        max_atom = float('inf')
    if min_time is None:
        min_time = 0.0
    if max_time is None:
        max_time = float('inf')

    data = []
    with open(file_path, 'r', encoding="utf-8") as f_source:
        read_data = f_source.readlines()

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
    val = binom.ppf(prob, n_trials, selection_prob)
    if isnan(val):
        raise Exception(
            f"Could not find maximum selected from {n_trials} out of"
            f" {n_total_trials} trials, with selection probability of"
            f" {selection_prob} and chance {chance}.  Final chance = {prob}.")
    return val


def get_probable_minimum_selected(
        n_total_trials, n_trials, selection_prob, chance=(1.0 / 100.0)):
    """ Get the likely minimum number of items that will be selected from a\
        set of n_trials from a total set of n_total_trials\
        with a probability of selection of selection_prob
    """
    prob = (chance / float(n_total_trials))
    return binom.ppf(prob, n_trials, selection_prob)


def get_probability_within_range(dist, lower, upper):
    """ Get the probability that a value will fall within the given range for\
        a given RandomDistribution
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.cdf(dist, upper) - stats.cdf(dist, lower)


def get_maximum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely maximum value of a RandomDistribution given a\
        number of draws
    """
    stats = STATS_BY_NAME[dist.name]
    prob = 1.0 - (chance / float(n_items))
    return stats.ppf(dist, prob)


def get_minimum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely minimum value of a RandomDistribution given a\
        number of draws
    """
    stats = STATS_BY_NAME[dist.name]
    prob = chance / float(n_items)
    return stats.ppf(dist, prob)


def get_mean(dist):
    """ Get the mean of a RandomDistribution
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.mean(dist)


def get_standard_deviation(dist):
    """ Get the standard deviation of a RandomDistribution
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.std(dist)


def get_variance(dist):
    """ Get the variance of a RandomDistribution
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.var(dist)


def high(dist):
    """ Gets the high or max boundary value for this distribution

    Could return None
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.high(dist)


def low(dist):
    """ Gets the high or min boundary value for this distribution

    Could return None
    """
    stats = STATS_BY_NAME[dist.name]
    return stats.low(dist)


def _validate_mars_kiss_64_seed(seed):
    """ Update the seed to make it compatible with the RNG algorithm
    """
    if seed[1] == 0:
        # y (<- seed[1]) can't be zero so set to arbitrary non-zero if so
        seed[1] = ARBITRARY_Y

    # avoid z=c=0 and make < 698769069
    seed[3] = seed[3] % MARS_C_MAX + 1
    return seed


def create_mars_kiss_seeds(rng):
    """ generates and checks that the seed values generated by the given\
        random number generator or seed to a random number generator are\
        suitable for use as a mars 64 kiss seed.

    :param rng: the random number generator.
    :type rng: ~numpy.random.RandomState
    :param seed:
        the seed to create a random number generator if not handed.
    :type seed: int or None
    :return: a list of 4 ints which are used by the mars64 kiss random number
        generator for seeds.
    :rtype: list(int)
    """
    kiss_seed = _validate_mars_kiss_64_seed([
        rng.randint(-BASE_RANDOM_FOR_MARS_64, CAP_RANDOM_FOR_MARS_64) +
        BASE_RANDOM_FOR_MARS_64 for _ in range(N_RANDOM_NUMBERS)])
    return kiss_seed


def get_n_bits(n_values):
    """ Determine how many bits are required for the given number of values

    :param int n_values: the number of values (starting at 0)
    :return: the number of bits required to express that many values
    :rtype: int
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log2(n_values)))


def moved_in_v6(old_location, _):
    """
    Tells the users that old code is no lonfger implemented

    :param str old_location: old import
    :raise: NotImplementedError
    """
    raise NotImplementedError("Old import: {}".format(old_location))


def moved_in_v7(old_location, new_location):
    """
    Warns the users that they are using an old import.

    In version 8 this will be upgraded to a exception and then later removed

    :param str old_location: old import
    :param str new_location: new import
    :raise: an exception if in CONTINUOUS_INTEGRATION
    """
    if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
        raise NotImplementedError("Old import: {}".format(old_location))
    logger.warning("File {} moved to {}. Please fix your imports. "
                   "In version 8 this will fail completely."
                   "".format(old_location, new_location))


def moved_in_v7_warning(message):
    """
    Warns the user that they are using old code

    In version 8 this will be upgraded to a exception and then later removed

    :param str message:
    """
    if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
        raise NotImplementedError(message)
    logger.warning(f"{message} In version 8 old call will fail completely.")


def get_time_to_write_us(n_bytes, n_cores):
    """ Determine how long a write of a given number of bytes will take in us

    :param int n_bytes: The number of bytes to transfer
    :param int n_cores: How many cores will be writing at the same time
    """
    bandwidth_per_core = WRITE_BANDWIDTH_BYTES_PER_SECOND / n_cores
    seconds = n_bytes / bandwidth_per_core
    return int(math.ceil(seconds * MICRO_TO_SECOND_CONVERSION))
