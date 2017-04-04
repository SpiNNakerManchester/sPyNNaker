"""
utility class containing simple helper methods
"""
from pyNN.random import RandomDistribution

from spynnaker.pyNN.utilities import globals_variables

from spinn_front_end_common.utilities import exceptions

import numpy
import os
import logging
import struct

from scipy.stats import binom

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
    if isinstance(param, RandomDistribution):

        if no_atoms > 1:
            return numpy.asarray(param.next(n=no_atoms), dtype="float")

        # numpy reduces a single valued array to a single value, so enforce
        # that it is an array
        return numpy.array([param.next(n=no_atoms)], dtype="float")

    # Deal with a single value by exploding to multiple values
    if not hasattr(param, '__iter__'):
        return numpy.array([param] * no_atoms, dtype="float")

    # Deal with multiple values, but not the correct number of them
    if len(param) != no_atoms:

        raise exceptions.ConfigurationException(
            "The number of params does not equal with the number of atoms in"
            " the vertex")

    # Deal with the correct number of multiple values
    return numpy.array(param, dtype="float")


def write_parameters_per_neuron(spec, vertex_slice, parameters):
    for atom in range(vertex_slice.lo_atom, vertex_slice.hi_atom + 1):
        for param in parameters:
            value = param.get_value()
            if hasattr(value, "__len__"):
                if len(value) > 1:
                    value = value[atom]
                else:
                    value = value[0]

            spec.write_value(data=value,
                             data_type=param.get_dataspec_datatype())


def translate_parameters(types, byte_array, offset, vertex_slice):
    """ Translate an array of data into a set of parameters

    :param types: the DataType of each of the parameters to translate
    :param byte_array: the byte array to read parameters out of
    :param offset: where in the byte array to start reading from
    :param vertex_slice: the map of atoms from a application vertex
    :return: An array of arrays of parameter values, and the new offset
    """

    # If there are no parameters, return an empty list
    if len(types) == 0:
        return numpy.zeros((0, 0), dtype="float"), offset

    # Get the single-struct format
    struct_data_format = ""
    for param_type in types:
        struct_data_format += param_type.struct_encoding

    # Get the struct-array format, consisting of repeating the struct
    struct_array_format = "<" + (struct_data_format * vertex_slice.n_atoms)

    # unpack the params from the byte array
    translated_parameters = numpy.asarray(
        struct.unpack_from(struct_array_format, byte_array, offset),
        dtype="float")

    # scale values with required scaling factor
    scales = numpy.tile(
        [float(param_type.scale) for param_type in types],
        vertex_slice.n_atoms)
    scaled_parameters = translated_parameters / scales

    # sort the parameters into arrays of values, one array per parameter
    sorted_parameters = scaled_parameters.reshape(
        (vertex_slice.n_atoms, len(types))).swapaxes(0, 1)

    # Get the size of the parameters read
    parameter_size = sum([param_type.size for param_type in types])

    return sorted_parameters, offset + (parameter_size * vertex_slice.n_atoms)


def get_parameters_size_in_bytes(parameters):
    """ Get the total size of a list of parameters in bytes

    :param parameters: the parameters to compute the total size of
    :return: size of all the parameters in bytes
    :rtype: int
    """
    total = 0
    for parameter in parameters:
        total += parameter.get_dataspec_datatype().size
    return total


def set_slice_values(arrays, values, vertex_slice):
    """ Set a vertex slice of atoms in a set of arrays to the given values

    :param array: The array of arrays to set the values in
    :param value: The array of arrays of values to set
    :param vertex_slice: The slice of parameters to set
    """
    for i, array in enumerate(arrays):
        array[vertex_slice.as_slice] = values[i]


def read_in_data_from_file(
        file_path, min_atom, max_atom, min_time, max_time):
    """ Read in a file of data values where the values are in a format of:
        <time>\t<atom id>\t<data value>

    :param file_path: absolute path to a file containing the data
    :param min_atom: min neuron id to which neurons to read in
    :param max_atom: max neuron id to which neurons to read in
    :param min_time: min time slot to read neurons values of.
    :param max_time: max time slot to read neurons values of.
    :return: a numpy array of (time stamp, atom id, data value)
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
    """ Read spikes from a file formatted as:
        <time>\t<neuron id>

    :param file_path: absolute path to a file containing spike values
    :param min_atom: min neuron id to which neurons to read in
    :param max_atom: max neuron id to which neurons to read in
    :param min_time: min time slot to read neurons values of.
    :param max_time: max time slot to read neurons values of.
    :param split_value: the pattern to split by
    :return:\
        a numpy array with max_atom elements each of which is a list of\
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


def validate_mars_kiss_64_seed(seed):
    """ Update the seed to make it compatible with the rng algorithm
    """
    if seed[1] == 0:

        # y (<- seed[1]) can't be zero so set to arbitrary non-zero if so
        seed[1] = 13031301

    # avoid z=c=0 and make < 698769069
    seed[3] = seed[3] % 698769068 + 1
