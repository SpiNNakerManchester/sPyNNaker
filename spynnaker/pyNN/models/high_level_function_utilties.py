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
        return translate_filter(neuron_filter, size, False)


def translate_filter_to_boolean_format(neuron_filter, size):
    """

    :param neuron_filter:
    :param size:
    :return:
    """
    return translate_filter(neuron_filter, size, True)


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

    elif isinstance(neuron_filter, int):
        if boolean_format:
            new_filter = list()
            for _ in range(0, size):
                    new_filter.append(False)
            new_filter[neuron_filter] = True
        else:
            new_filter = [neuron_filter]

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
        pop_view_atom.initialize(variable, atom_variable)


def _set_parameters(variable, value, atoms):
    """

    :param variable: the variable to set
    :param value: the value to set the parameter to
    :param atoms:  the atoms to set
    :param size: the number of neurons that need to be set.
    :return: None
    """
    # expand variables
    variables_for_atoms = \
        utility_calls.convert_param_to_numpy(value, len(atoms))

    # set params
    for atom_variable, pop_view_atom in zip(variables_for_atoms, atoms):
        pop_view_atom.set_param(variable, atom_variable)


def set_parameters(param, val, atoms, mapped_vertices, class_object):
    """
    private method for :
    Set one or more parameters for every cell in the population.

    param can be a dict, in which case value should not be supplied, or a
    string giving the parameter name, in which case value is the parameter
    value. value can be a numeric value, or list of such
    (e.g. for setting spike times)::

      p.set("tau_m", 20.0).
      p.set({'tau_m':20, 'v_rest':-65})
    :param param: the parameter to set
    :param val: the value of the parameter to set.
    """
    found = False

    bits_to_check = [
        class_object.neuron_model, class_object.input_type,
        class_object.threshold_type, class_object.synapse_type]

    if hasattr(class_object, "additional_input"):
        bits_to_check.append(class_object.additional_input)

    for obj in bits_to_check:
        if type(param) is str:
            if hasattr(obj, param):
                found = True
        elif type(param) is not dict:
            raise Exception(
                "Error: invalid parameter type for set() function for "
                "population parameter. Exiting.")
        else:
            # Add a dictionary-structured set of new parameters to the
            # current set: get atoms in pop view
            for (key, value) in param.iteritems():
                if hasattr(obj, key):
                    found = True
    if not found:

        raise exceptions.ConfigurationException(
            "Type {} does not have parameter {}".format(
                class_object.model_name, param))

    if type(param) is str:
        if val is None:
            raise Exception("Error: No value given in set() function for "
                            "population parameter. Exiting.")
        _set_parameters(param, val, atoms)

    elif type(param) is not dict:
            raise Exception("Error: invalid parameter type for "
                            "set() function for population parameter."
                            " Exiting.")

    elif mapped_vertices is not None:
        (vertex, _, _) = mapped_vertices
        for (key, value) in param.iteritems():
            vertex.set_value(key, value)
    else:
        # Add a dictionary-structured set of new parameters to the
        # current set: get atoms in pop view
        for (key, value) in param.iteritems():
            _set_parameters(key, value, atoms)