"""
utility class containing simple helper methods
"""
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import RandomDistribution
from data_specification import constants as ds_constants
from spynnaker.pyNN import exceptions
import numpy
import math
import os
import logging
import inspect


logger = logging.getLogger(__name__)


def check_directory_exists_and_create_if_not(filename):
    components = os.path.abspath(filename).split(os.sep)
    directory = os.path.abspath(os.path.join(os.sep,
                                             *components[1:len(components)-1]))
    #check if directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)


def is_conductance(population):
    raise NotImplementedError


def check_weight(weight, synapse_type, is_conductance_type):
    raise NotImplementedError


def check_delay(delay):
    raise NotImplementedError


def get_region_base_address_offset(app_data_base_address, region):
    return (app_data_base_address +
            ds_constants.APP_PTR_TABLE_HEADER_BYTE_SIZE + (region * 4))

def convert_param_to_numpy(param, no_atoms):
    """
    converts parameters into numpy arrays as needed
    """
    if RandomDistribution is None:
        raise exceptions.ConfigurationException(
            "Missing PyNN. Please install version 0.7.5 from "
            "http://neuralensemble.org/PyNN/")
    if isinstance(param, RandomDistribution):
        return numpy.asarray(param.next(n=no_atoms))
    elif not hasattr(param, '__iter__'):
        return numpy.array([param], dtype=float)
    elif len(param) != no_atoms:
        raise exceptions.ConfigurationException("The number of params does"
                                                " not equal with the number"
                                                " of atoms in the vertex ")
    else:
        return numpy.array(param, dtype=float)