"""
utility class containing simple helper methods
"""
from spynnaker.pyNN.utilities.random_stats.random_stats_scipy_impl \
    import RandomStatsScipyImpl
from spynnaker.pyNN.utilities.random_stats.random_stats_uniform_impl \
    import RandomStatsUniformImpl
from spinn_front_end_common.utilities import exceptions
import numpy
import os
import logging

from scipy.stats import binom

try:
    from pyNN.random import RandomDistribution
except ImportError:
    RandomDistribution = None


logger = logging.getLogger(__name__)


def check_directory_exists_and_create_if_not(filename):
    """
    helper method for checking if a directory exists, and if not, create it
    :param filename:
    :return:
    """
    directory = os.path.dirname(filename)
    if directory != "" and not os.path.exists(directory):
        os.makedirs(directory)


def convert_param_to_numpy(param, no_atoms, is_array=False):
    """
    converts parameters into numpy arrays as needed
    :param param: the param to convert
    :param no_atoms: the number of atoms available for conversion of param
    :return the converted param in whatever format it was given
    """
    if RandomDistribution is None:
        raise exceptions.ConfigurationException(
            "Missing PyNN. Please install version 0.7.5 from "
            "http://neuralensemble.org/PyNN/")
    if isinstance(param, RandomDistribution):
        if no_atoms > 1:
            return numpy.asarray(param.next(n=no_atoms), dtype="float")
        else:
            return numpy.array([param.next(n=no_atoms)], dtype="float")
    elif not hasattr(param, '__iter__'):
        if param is None:
            return [None] * no_atoms
        else:
            return numpy.array([param] * no_atoms, dtype="float")
    elif is_array:
        if hasattr(param[0], '__len__'):
            if len(param) != no_atoms:
                raise exceptions.ConfigurationException(
                    "The number of params does not equal with the number of"
                    " atoms in the vertex ")
            # converts the parameter into a numpy array of floats.
            return [numpy.array(arr, dtype="float") for arr in param]
        else:
            # need to go from [1,2,3] to [[1,2,3],[1,2,3],[1,2,3]] for n atoms
            # worth. This is done through the use of numpy.tile which takes
            # the array converted to float and duplicated n_atoms time in the
            # virtual dimension.
            return numpy.tile(numpy.array(param, dtype="float"), (no_atoms, 1))

    else:
        if len(param) != no_atoms:
            raise exceptions.ConfigurationException(
                "The number of params does not equal with the number "
                "of atoms in the vertex ")
        return numpy.array(param, dtype="float")


def write_parameters_per_neuron(spec, vertex_slice, parameter_call):
    for atom in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
        params = parameter_call(atom)
        for param in params:
            value = param.get_value()
            spec.write_value(data=value,
                             data_type=param.get_dataspec_datatype())


def read_in_data_from_file(
        file_path, min_atom, max_atom, min_time, max_time):
    """method for helping code read in files of data values where the values are
    in a format of <Time><tab><atom_id><tab><data_value>

    :param file_path: absolute filepath to a file where gsyn values have been
    written
    :param min_atom: min neuron id to which neurons to read in
    :param max_atom: max neuron id to which neurons to read in
    :param min_time: min time slot to read neurons values of.
    :param max_time:max time slot to read neurons values of.
    :return: a numpi destacked array containing time stamps, neuron id and the
    data value.
    """
    times = list()
    atom_ids = list()
    data_items = list()

    with open(file_path, 'r') as fsource:
            read_data = fsource.readlines()

    for line in read_data:
        if not line.startswith('#'):
            values = line.split("\t")
            neuron_id = int(eval(values[1]))
            time = float(eval(values[0]))
            data_value = float(eval(values[2]))
            if (min_atom <= neuron_id < max_atom and
                    min_time <= time < max_time):
                times.append(time)
                atom_ids.append(neuron_id)
                data_items.append(data_value)

            else:
                print "failed to enter {}:{}".format(neuron_id, time)

    result = numpy.dstack((atom_ids, times, data_items))[0]
    result = result[numpy.lexsort((times, atom_ids))]
    return result


def read_spikes_from_file(file_path, min_atom, max_atom, min_time, max_time,
                          split_value="\t"):
    """
    helper method for reading spikes from a file
    :param file_path: absolute filepath to a file where spike values have been
    written
    :param min_atom: min neuron id to which neurons to read in
    :param max_atom: max neuron id to which neurons to read in
    :param min_time: min time slot to read neurons values of.
    :param max_time:max time slot to read neurons values of.
    :param split_value: the pattern to split by
    :return: a numpi destacked array containing time stamps, neuron id and the
    spike times.
    """
    with open(file_path, 'r') as fsource:
            read_data = fsource.readlines()

    data = dict()
    max_atom_found = 0
    for line in read_data:
        if not line.startswith('#'):
            values = line.split(split_value)
            time = float(eval(values[0]))
            neuron_id = int(eval(values[1]))
            if ((min_atom is None or min_atom <= neuron_id) and
                    (max_atom is None or neuron_id < max_atom) and
                    (min_time is None or min_time <= time) and
                    (max_time is None or time < max_time)):
                if neuron_id not in data:
                    data[neuron_id] = list()
                data[neuron_id].append(time)
                if max_atom is None and neuron_id > max_atom_found:
                    max_atom_found = neuron_id

    if max_atom is None:
        result = numpy.ndarray(shape=max_atom_found, dtype=object)
    else:
        result = numpy.ndarray(shape=max_atom, dtype=object)
    for neuron_id in range(0, max_atom):
        if neuron_id in data:
            result[neuron_id] = data[neuron_id]
        else:
            result[neuron_id] = list()
    return result


# Converts between a distribution name, and the appropriate scipy stats for\
# that distribution
_distribution_to_stats = {
    'binomial': RandomStatsScipyImpl("binom"),
    'gamma': RandomStatsScipyImpl("gamma"),
    'exponential': RandomStatsScipyImpl("expon"),
    'lognormal': RandomStatsScipyImpl("lognorm"),
    'normal': RandomStatsScipyImpl("norm"),
    'poisson': RandomStatsScipyImpl("poisson"),
    'uniform': RandomStatsUniformImpl(),
    'randint': RandomStatsScipyImpl("randint"),
    'vonmises': RandomStatsScipyImpl("vonmises"),
}


def get_probable_maximum_selected(
        n_total_selections, n_selected, selection_prob, chance=(1.0 / 100.0)):
    """ Get the likely maximum number of items that will be selected from a\
        set of n_selected from a total set of n_total_selections\
        with a probability of selection of selection_prob
    """
    prob = 1.0 - (chance / float(n_total_selections))
    return binom.ppf(prob, n_selected, selection_prob)


def get_probability_within_range(dist, lower, upper):
    """ Get the probability that a value will fall within the given range for\
        a given RandomDistribution dist
    """
    stats = _distribution_to_stats[dist.name]
    return (stats.cdf(dist, upper) - stats.cdf(dist, lower))


def get_maximum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely maximum value of a RandomDistribution given a\
        number of draws
    """
    stats = _distribution_to_stats[dist.name]
    prob = 1.0 - (chance / float(n_items))
    return stats.ppf(dist, prob)


def get_minimum_probable_value(dist, n_items, chance=(1.0 / 100.0)):
    """ Get the likely minimum value of a RandomDistribution given a\
        number of draws
    """
    stats = _distribution_to_stats[dist.name]
    prob = chance / float(n_items)
    return stats.ppf(dist, prob)


def get_mean(dist):
    """ Get the mean of a RandomDistribution
    """
    stats = _distribution_to_stats[dist.name]
    return stats.mean(dist)


def get_standard_deviation(dist):
    """ Get the standard deviation of a RandomDistribution
    """
    stats = _distribution_to_stats[dist.name]
    return stats.std(dist)


def get_variance(dist):
    """ Get the variance of a RandomDistribution
    """
    stats = _distribution_to_stats[dist.name]
    return stats.var(dist)
