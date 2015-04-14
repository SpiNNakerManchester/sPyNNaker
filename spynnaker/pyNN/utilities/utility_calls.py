"""
utility class containing simple helper methods
"""
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import RandomDistribution
from data_specification import constants as ds_constants
from spinn_front_end_common.utilities import exceptions
import numpy
import os
import logging


logger = logging.getLogger(__name__)


def check_directory_exists_and_create_if_not(filename):
    """
    helper method for checking if a directory exists, and if not, create it
    :param filename:
    :return:
    """
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)


def check_weight(weight, synapse_type, is_conductance_type):
    raise NotImplementedError


def check_delay(delay):
    raise NotImplementedError


def convert_param_to_numpy(param, no_atoms):
    """
    converts parameters into numpy arrays as needed
    :param param: the param to convert
    :param no_atoms: the number of atoms avilable for conversion of param
    :return the converted param in whatever format it was given
    """
    if RandomDistribution is None:
        raise exceptions.ConfigurationException(
            "Missing PyNN. Please install version 0.7.5 from "
            "http://neuralensemble.org/PyNN/")
    if isinstance(param, RandomDistribution):
        if no_atoms > 1:
            return numpy.asarray(param.next(n=no_atoms))
        else:
            return numpy.array([param.next(n=no_atoms)])
    elif not hasattr(param, '__iter__'):
        return numpy.array([param], dtype=float)
    elif len(param) != no_atoms:
        raise exceptions.ConfigurationException("The number of params does"
                                                " not equal with the number"
                                                " of atoms in the vertex ")
    else:
        return numpy.array(param, dtype=float)
