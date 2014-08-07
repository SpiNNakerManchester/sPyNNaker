"""
utility class containing simple helper methods
"""
from spynnaker.pyNN.models.neural_properties.randomDistributions \
    import RandomDistribution
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
    return app_data_base_address + 16 + region * 4


def get_ring_buffer_to_input_left_shift(subvertex, sub_graph):
    in_sub_edges = sub_graph.incoming_subedges_from_subvertex(subvertex)
    total_exc_weights = numpy.zeros(subvertex.n_atoms)
    total_inh_weights = numpy.zeros(subvertex.n_atoms)
    for subedge in in_sub_edges:
        sublist = subedge.get_synapse_sublist()
        sublist.sum_weights(total_exc_weights, total_inh_weights)

    max_weight = max((max(total_exc_weights), max(total_inh_weights)))
    max_weight_log_2 = 0
    if max_weight > 0:
        max_weight_log_2 = math.log(max_weight, 2)

    # Currently, we can only cope with positive left shifts, so the minimum
    # scaling will be no shift i.e. a max weight of 0nA
    if max_weight_log_2 < 0:
        max_weight_log_2 = 0

    max_weight_power = int(math.ceil(max_weight_log_2))

    logger.debug("Max weight is {}, Max power is {}"
                 .format(max_weight, max_weight_power))

    # Actual shift is the max_weight_power - 1 for 16-bit fixed to s1615,
    # but we ignore the "-1" to allow a bit of overhead in the above
    # calculation in case a couple of extra spikes come in
    return max_weight_power


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


def locate_all_subclasses_of(class_to_find_subclasses_of):
    #find all constraints!
    subclass_list = list()
    current_subclass_list = class_to_find_subclasses_of.__subclasses__()
    while len(current_subclass_list) != 0:
        current_class = current_subclass_list[0]
        #todo make this work so it doesnt just return false all the bloody time!!!!
        if not inspect.isabstract(current_class):
            subclass_list.append(current_class)
        current_subclass_list.remove(current_class)
        for new_found_class in current_class.__subclasses__():
            current_subclass_list.append(new_found_class)
    return subclass_list