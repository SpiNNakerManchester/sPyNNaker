# Copyright (c) 2014 The University of Manchester
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

"""
Utility package containing simple helper functions.
"""
import logging
import os
import math
import neo
import numpy
from numpy import uint32, floating
from numpy.typing import NDArray
from math import isnan
from pyNN.random import RandomDistribution
from typing import List, Tuple
from scipy.stats import binom
from spinn_utilities.log import FormatAdapter
from spinn_utilities.safe_eval import SafeEval
from spinn_utilities.config_holder import get_config_bool
from spinn_utilities.logger_utils import warn_once
from spinn_front_end_common.interface.ds import DataType
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


def check_directory_exists_and_create_if_not(filename: str):
    """
    Create a parent directory for a file if it doesn't exist.

    :param str filename: The file whose parent directory is to be created
    """
    directory = os.path.dirname(filename)
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)


def convert_param_to_numpy(param, no_atoms: int) -> NDArray[floating]:
    """
    Convert parameters into numpy arrays.

    :param param: the param to convert
    :type param: ~pyNN.random.RandomDistribution or int or float or list(int)
        or list(float) or ~numpy.ndarray
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
            return numpy.array(param_value, dtype=floating)
        return numpy.array([param_value], dtype=floating)

    # Deal with a single value by exploding to multiple values
    if not hasattr(param, '__iter__'):
        return numpy.array([param] * no_atoms, dtype=floating)

    # Deal with multiple values, but not the correct number of them
    if len(param) != no_atoms:
        raise ConfigurationException(
            "The number of params does not equal with the number of atoms in"
            " the vertex")

    # Deal with the correct number of multiple values
    return numpy.array(param, dtype=floating)


def convert_to(value, data_type: DataType) -> uint32:
    """
    Convert a value to a given data type.

    :param value: The value to convert
    :param ~data_specification.enums.DataType data_type:
        The data type to convert to
    :return: The converted data as a numpy data type
    :rtype: numpy.uint32
    """
    return numpy.round(data_type.encode_as_int(value)).astype(
        data_type.struct_encoding)


def read_in_data_from_file(
        file_path: str, min_atom: int, max_atom: int,
        min_time: float, max_time: float, extra: bool = False) -> NDArray:
    """
    Read in a file of data values where the values are in a format of::

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
    times: List[float] = []
    atom_ids: List[int] = []
    data_items: List[float] = []
    evaluator = SafeEval()
    with open(file_path, 'r', encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            if extra:
                time_s, neuron_id_s, data_value_s, _extra = line.split("\t")
            else:
                time_s, neuron_id_s, data_value_s = line.split("\t")
            time = float(evaluator.eval(time_s))
            neuron_id = int(evaluator.eval(neuron_id_s))
            data_value = float(evaluator.eval(data_value_s))
            if (min_atom <= neuron_id < max_atom and
                    min_time <= time < max_time):
                times.append(time)
                atom_ids.append(neuron_id)
                data_items.append(data_value)
            else:
                print(f"failed to enter {neuron_id}:{time}")

    result = numpy.dstack((atom_ids, times, data_items))[0]
    return result[numpy.lexsort(result.T[1::-1])]


def read_spikes_from_file(
        file_path: str,
        min_atom: float = 0, max_atom: float = float('inf'),
        min_time: float = 0, max_time: float = float('inf'),
        split_value: str = "\t") -> NDArray[numpy.integer]:
    """
    Read spikes from a file formatted as::

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
        a numpy array with up to max_atom elements each of which is a list of
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
    """
    Get the likely maximum number of items that will be selected from a
    set of `n_trials` from a total set of `n_total_trials`
    with a probability of selection of `selection_prob`.
    """
    prob = 1.0 - (chance / float(n_total_trials))
    val = binom.ppf(prob, n_trials, selection_prob)
    if isnan(val):
        raise ValueError(
            f"Could not find maximum selected from {n_trials} out of"
            f" {n_total_trials} trials, with selection probability of"
            f" {selection_prob} and chance {chance}.  Final chance = {prob}.")
    return val


def get_probable_minimum_selected(
        n_total_trials, n_trials, selection_prob, chance=(1.0 / 100.0)):
    """
    Get the likely minimum number of items that will be selected from a
    set of `n_trials` from a total set of `n_total_trials`
    with a probability of selection of `selection_prob`.
    """
    prob = (chance / float(n_total_trials))
    return binom.ppf(prob, n_trials, selection_prob)


def get_probability_within_range(distribution, lower, upper):
    """
    Get the probability that a value will fall within the given range for
    a given RandomDistribution.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    :param float lower:
    :param float upper:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.cdf(distribution, upper) - stats.cdf(distribution, lower)


def get_maximum_probable_value(distribution, n_items, chance=(1.0 / 100.0)):
    """
    Get the likely maximum value of a RandomDistribution given a
    number of draws.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    :param int n_items:
    :param float chance:
    """
    stats = STATS_BY_NAME[distribution.name]
    prob = 1.0 - (chance / float(n_items))
    return stats.ppf(distribution, prob)


def get_minimum_probable_value(distribution, n_items, chance=(1.0 / 100.0)):
    """
    Get the likely minimum value of a RandomDistribution given a
    number of draws.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    prob = chance / float(n_items)
    return stats.ppf(distribution, prob)


def get_mean(distribution):
    """
    Get the mean of a RandomDistribution.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.mean(distribution)


def get_standard_deviation(distribution):
    """
    Get the standard deviation of a RandomDistribution.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.std(distribution)


def get_variance(distribution):
    """
    Get the variance of a RandomDistribution.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.var(distribution)


def high(distribution):
    """
    Gets the high or maximum boundary value for this distribution.

    Could return `None`.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.high(distribution)


def low(distribution):
    """
    Gets the high or minimum boundary value for this distribution.

    Could return `None`.

    :param ~spynnaker.pyNN.RandomDistribution distribution:
    """
    stats = STATS_BY_NAME[distribution.name]
    return stats.low(distribution)


def _validate_mars_kiss_64_seed(seed: List[int]) -> List[int]:
    """
    Update the seed to make it compatible with the RNG algorithm.
    """
    if seed[1] == 0:
        # y (<- seed[1]) can't be zero so set to arbitrary non-zero if so
        seed[1] = ARBITRARY_Y

    # avoid z=c=0 and make < 698769069
    seed[3] = seed[3] % MARS_C_MAX + 1
    return seed


def create_mars_kiss_seeds(rng) -> Tuple[int, ...]:
    """
    Generates and checks that the seed values generated by the given
    random number generator or seed to a random number generator are
    suitable for use as a mars 64 kiss seed.

    :param rng: the random number generator.
    :type rng: ~numpy.random.RandomState
    :param seed:
        the seed to create a random number generator if not handed.
    :type seed: int or None
    :return: a list of 4 integers which are used by the mars64 kiss random
        number generator for seeds.
    :rtype: list(int)
    """
    kiss_seed = _validate_mars_kiss_64_seed([
        rng.randint(-BASE_RANDOM_FOR_MARS_64, CAP_RANDOM_FOR_MARS_64) +
        BASE_RANDOM_FOR_MARS_64 for _ in range(N_RANDOM_NUMBERS)])
    return tuple(kiss_seed)


def get_n_bits(n_values):
    """
    Determine how many bits are required for the given number of values.

    :param int n_values: the number of values (starting at 0)
    :return: the number of bits required to express that many values
    :rtype: int
    """
    if n_values == 0:
        return 0
    if n_values == 1:
        return 1
    return int(math.ceil(math.log2(n_values)))


def get_time_to_write_us(n_bytes, n_cores):
    """
    Determine how long a write of a given number of bytes will take in us.

    :param int n_bytes: The number of bytes to transfer
    :param int n_cores: How many cores will be writing at the same time
    """
    bandwidth_per_core = WRITE_BANDWIDTH_BYTES_PER_SECOND / n_cores
    seconds = n_bytes / bandwidth_per_core
    return int(math.ceil(seconds * MICRO_TO_SECOND_CONVERSION))


def get_neo_io(file_or_folder):
    """
    Hack for https://github.com/NeuralEnsemble/python-neo/issues/1287

    In Neo 0.12 neo.get_io only works with existing files

    :param str file_or_folder:
    """
    try:
        return neo.get_io(file_or_folder)
    except ValueError as ex:
        try:
            _, suffix = os.path.splitext(file_or_folder)
            suffix = suffix[1:].lower()
            # pylint: disable=no-member
            if suffix in neo.io_by_extension:
                writer_list = neo.io_by_extension[suffix]
                return writer_list[0](file_or_folder)
        except AttributeError:
            # for older neo which has no io_by_extension
            pass
        raise ex


def report_non_spynnaker_pyNN(msg):
    """
    Report a case of non-spynnaker-compatible PyNN being used.  This will warn
    or error depending on the configuration setting.

    :param str msg: The message to report
    """
    if get_config_bool("Simulation", "error_on_non_spynnaker_pynn"):
        raise ConfigurationException(msg)
    else:
        warn_once(logger, msg)


def check_rng(rng, where):
    """
    Check for non-None rng parameter since this is no longer compatible with
    sPyNNaker.  If not None, warn or error depending on a config value.

    :param rng: The rng parameter value.
    """
    if rng is not None and rng.seed is not None:
        report_non_spynnaker_pyNN(
            f"Use of rng in {where} is not supported in sPyNNaker in this"
            " case. Please instead use seed=<seed> in the target Population to"
            " ensure random numbers are seeded.")
