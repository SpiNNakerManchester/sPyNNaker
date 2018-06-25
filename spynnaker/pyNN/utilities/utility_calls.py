"""
utility class containing simple helper methods
"""
import numpy
import os
import logging
import struct

from spinn_utilities.safe_eval import SafeEval

from scipy.stats import binom
from spinn_front_end_common.utilities import globals_variables
from spinn_front_end_common.utilities.exceptions import ConfigurationException
from decimal import Decimal

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


def write_parameters_per_neuron(spec, vertex_slice, parameters,
                                slice_paramaters=False):
    """
    Writes the parameters neurons by neuron

    :param spec: The data specification to write to
    :param vertex_slice: The vertex currently being written
    :param parameters: The parameters currently being written
    :param slice_paramaters: Flag to indicate if the parameters are only for\
        this slice.

        The default False say that the parameters are for full\
        lists across all slices. So that parameter[x] will be for the neuron\
        x where x is the id which may or may nor be in the slice.

        If True the parameter list will only contain values for this slice.\
        So that parameter[x] is the x'th neuron in the slice.\
        i.e. the neuron with the id x + vertex_slice.lo_atom
    """
    if len(parameters) == 0:
        return

    # Get an iterator per parameter
    iterators = []
    for param in parameters:
        if slice_paramaters:
            iterators.append(param.iterator_by_slice(
                0, vertex_slice.n_atoms, spec))
        else:
            iterators.append(param.iterator_by_slice(
                vertex_slice.lo_atom, vertex_slice.hi_atom + 1, spec))

    # Iterate through the iterators until a StopIteration is generated
    while True:
        try:
            for iterator in iterators:
                (cmd_word_list, cmd_string) = next(iterator)
                spec.write_command_to_files(cmd_word_list, cmd_string)
        except StopIteration:
            return


def translate_parameters(types, byte_array, offset, vertex_slice):
    """ Translate an array of data into a set of parameters

    :param types: the DataType of each of the parameters to translate
    :param byte_array: the byte array to read parameters out of
    :param offset: where in the byte array to start reading from
    :param vertex_slice: the map of atoms from a application vertex
    :return: An array of arrays of parameter values, and the new offset
    """

    # If there are no parameters, return an empty list
    if not types:
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
    parameter_size = sum(param_type.size for param_type in types)

    return sorted_parameters, offset + (parameter_size * vertex_slice.n_atoms)


def convert_to(value, data_type):
    """ Convert a value to a given data type

    :param value: The value to convert
    :param data_type: The data type to convert to
    :return: The converted data as a numpy data type
    """
    return numpy.round(
        Decimal(str(value)) * data_type.scale).astype(
            numpy.dtype(data_type.structencoding))


def get_parameters_size_in_bytes(parameters):
    """ Get the total size of a list of parameters in bytes

    :param parameters: the parameters to compute the total size of
    :return: size of all the parameters in bytes
    :rtype: int
    """
    return sum(param.get_dataspec_datatype().size for param in parameters)


def set_slice_values(arrays, values, vertex_slice):
    """ Set a vertex slice of atoms in a set of arrays to the given values

    :param array: The array of arrays to set the values in
    :param value: The array of arrays of values to set
    :param vertex_slice: The slice of parameters to set
    """
    for i, array in enumerate(arrays):
        array[vertex_slice.as_slice] = values[i]


def read_in_data_from_file(
        file_path, min_atom, max_atom, min_time, max_time, extra=False):
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
        <time>\t<neuron id>
    :param file_path: absolute path to a file containing spike values
    :type file_path: str
    :param min_atom: min neuron id to which neurons to read in
    :type min_atom: int
    :param max_atom: max neuron id to which neurons to read in
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
    :rtype: numpy array of (int, int)
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
