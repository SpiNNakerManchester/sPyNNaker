"""
utility class contianing simple helper methods
"""
import os
from spynnaker.pyNN.utilities.constants import \
    SV_VCPU, SIZEOF_VCPU, VCPU_OFFSETS
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import RandomDistribution
from spynnaker.pyNN import exceptions
import numpy


def check_directory_exists(filename):
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


def _get_vcp_item_offset(core, item):
    return SV_VCPU + (SIZEOF_VCPU * core) + VCPU_OFFSETS[item]


def get_app_data_base_address_offset(core):
    return _get_vcp_item_offset(core, "user0")


def get_region_base_address_offset(app_data_base_address, region):
    return app_data_base_address + 16 + region * 4


@staticmethod
def convert_param_to_numpy(param, no_atoms):
        """
        converts parameters into numpy arrays as needed
        """
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