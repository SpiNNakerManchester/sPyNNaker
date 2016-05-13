# front end common imports
from spinn_front_end_common.utilities import exceptions
from spynnaker.pyNN.utilities import utility_calls


def translate_filter_to_ints(neuron_filter, size):
        """
        translates filter from bool / slice / index into index
        :param neuron_filter:
        :param size:
        :return: None
        """
        translate_filter(neuron_filter, size, False)


def translate_filter_to_boolean_format(neuron_filter, size):
    """

    :param neuron_filter:
    :param size:
    :return:
    """
    translate_filter(neuron_filter, size, True)


def translate_filter(neuron_filter, size, boolean_format):
    """

    :param neuron_filter:
    :param size:
    :param boolean_format:
    :return:
    """
    new_filter = None

    # filter slice based filter into index's
    if isinstance(neuron_filter, slice):
        if not boolean_format:
            new_filter = _convert_slice_into_index_list(neuron_filter, size)
        else:
            new_filter = _convert_slice_into_index_boolean_list(
                neuron_filter, size)

    # check for bool based filter
    elif len(neuron_filter) != 0:

        # if bool based filter, convert into index's based.
        if isinstance(neuron_filter[0], bool):

            # test the bool filters length to work correctly.
            if len(neuron_filter) != size:
                raise exceptions.ConfigurationException(
                    "The bool array must be the same size as the parent "
                    "population /population view")

            # convert into indices
            new_filter = list()
            for index in range(0, len(neuron_filter)):
                if neuron_filter[index]:
                    new_filter.append(index)
            neuron_filter = new_filter

        # not bool or int, blow up
        elif not isinstance(neuron_filter[0], int):
            raise exceptions.ConfigurationException(
                "The population view filter can only be either:"
                "1. a slice, 2. a array of ints, a array of booleans.")
        else:
            if boolean_format:
                new_filter = list()
                for _ in range(0, size):
                    new_filter.append(False)
                for id in neuron_filter:
                    new_filter[id] = True
            else:
                new_filter = neuron_filter
    # not a bool, int, or a slice. blow up
    else:
        raise exceptions.ConfigurationException(
            "The population view filter can only be either:"
            "1. a slice, 2. a array of ints, a array of booleans.")

    return new_filter


def _convert_slice_into_index_list(slice_object, size):
    """
    :param slice_object: the slice
    :param size: the size of the pop to slice into
    :return: the new filter of index's
    """
    position = slice_object.start
    new_filter = list()
    while position < slice_object.stop:
        if 0 < position < size:
            new_filter.append(position)
            position += slice_object.step
    return new_filter


def _convert_slice_into_index_boolean_list(slice_object, size):
    """

    :param slice_object:
    :param size:
    :return:
    """

    position = slice_object.start
    new_filter = list()
    while position < slice_object.stop:
        # handle true
        if 0 < position < size:
            new_filter.append(True)

            # handle false's
            left_over = size - position
            if left_over != 0 and left_over > slice_object.step:
                for index in range(0, slice_object.step):
                    new_filter.append(False)
            if left_over != 0 and left_over < slice_object.step:
                for index in range(0, left_over):
                    new_filter.append(False)
    return new_filter


def initialize_parameters(variable, value, atoms, size):
    """

    :param variable: the variable to set
    :param value: the value to set the parameter to
    :param atoms:  the atoms to set
    :param size: the number of neurons that need to be set.
    :return: None
    """

    # expand variables
    variables_for_atoms = utility_calls.convert_param_to_numpy(value, size)

    # set params
    for atom_variable, pop_view_atom in zip(variables_for_atoms, atoms):
        pop_view_atom.set_param(variable, atom_variable)
