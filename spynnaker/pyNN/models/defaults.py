# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
from spinn_utilities.log import FormatAdapter
import logging

logger = FormatAdapter(logging.getLogger(__name__))


def _check_args(args_to_find, default_args, init):
    for arg in args_to_find:
        if arg not in default_args:
            raise AttributeError(
                "Argument {} not found, or no default value provided in {}"
                .format(arg, init))


def get_dict_from_init(init, skip=None, include=None):
    """ Get an argument initialisation dictionary by examining an \
        ``__init__`` method or function.

    :param callable init: The method.
    :param frozenset(str) skip: The arguments to be skipped, if any
    :param frozenset(str) include: The arguments that must be present, if any
    :return: an initialisation dictionary
    :rtype: dict(str, Any)
    """
    init_args = inspect.getfullargspec(init)
    n_defaults = 0 if init_args.defaults is None else len(init_args.defaults)
    n_args = 0 if init_args.args is None else len(init_args.args)
    default_args = ([] if init_args.args is None else
                    init_args.args[n_args - n_defaults:])
    default_values = [] if init_args.defaults is None else init_args.defaults

    # Check that included / skipped things exist
    if include is not None:
        _check_args(include, default_args, init)
    if skip is not None:
        _check_args(skip, default_args, init)

    return {arg: value
            for arg, value in zip(default_args, default_values)
            if ((arg != "self") and
                (skip is None or arg not in skip) and
                (include is None or arg in include))}


def default_parameters(parameters):
    """ Specifies arguments which are parameters.  Only works on the \
        ``__init__`` method of a class that is additionally decorated with\
        :py:meth:`defaults`

    :param iterable(str) parameters:
        The names of the arguments that are parameters
    """
    def wrap(method):
        # pylint: disable=protected-access
        # Find the real method in case we use multiple of these decorators
        wrapped = method
        while hasattr(method, "_method"):
            method = getattr(method, "_method")

        # Set the parameters of the method to be used later
        method._parameters = frozenset(parameters)
        method_args = inspect.getfullargspec(method)

        def wrapper(*args, **kwargs):
            # Check for state variables that have been specified in cell_params
            args_provided = method_args.args[:len(args)]
            args_provided.extend([
                arg for arg in kwargs.keys() if arg in method_args.args])
            for arg in args_provided:
                if arg not in method._parameters and arg != "self":
                    logger.warning(
                        "Formal PyNN specifies that {} should be set using "
                        "initial_values not cell_params".format(arg))
            wrapped(*args, **kwargs)

        # Store the real method in the returned object
        wrapper._method = method
        return wrapper
    return wrap


def default_initial_values(state_variables):
    """ Specifies arguments which are state variables.  Only works on the\
        ``__init__`` method of a class that is additionally decorated with\
        :py:meth:`defaults`

    :param iterable(str) state_variables:
        The names of the arguments that are state variables
    """
    def wrap(method):
        # pylint: disable=protected-access
        # Find the real method in case we use multiple of these decorators
        wrapped = method
        while hasattr(method, "_method"):
            method = getattr(method, "_method")

        # Store the state variables of the method to be used later
        method._state_variables = frozenset(state_variables)
        method_args = inspect.getfullargspec(method)

        def wrapper(*args, **kwargs):
            # Check for state variables that have been specified in cell_params
            args_provided = method_args.args[:len(args)]
            args_provided.extend([
                arg for arg in kwargs.keys() if arg in method_args.args])
            for arg in args_provided:
                if arg in method._state_variables:
                    logger.warning(
                        "Formal PyNN specifies that {} should be set using "
                        "initial_values not cell_params".format(arg))
            wrapped(*args, **kwargs)

        # Store the real method in the returned object
        wrapper._method = method
        return wrapper
    return wrap


def defaults(cls):
    """ Get the default parameters and state variables from the arguments to\
        the ``__init__`` method.  This uses the decorators\
        :py:func:`default_parameters` and :py:func:`default_initial_values` to\
        determine the parameters and state variables respectively.\
        If only one is specified, the other is assumed to be the remaining\
        arguments.\
        If neither are specified, it is assumed that all default arguments are\
        parameters.
    """
    if not inspect.isclass(cls):
        raise TypeError(f"{cls} is not a class")
    if not hasattr(cls, "__init__"):
        raise AttributeError("No __init__ found in {}".format(cls))
    init = getattr(cls, "__init__")
    while hasattr(init, "_method"):
        init = getattr(init, "_method")
    params = None
    if hasattr(init, "_parameters"):
        params = getattr(init, "_parameters")
    svars = None
    if hasattr(init, "_state_variables"):
        svars = getattr(init, "_state_variables")
    if params is None and svars is None:
        cls.default_parameters = get_dict_from_init(init)
        cls.default_initial_values = {}
    elif params is None:
        cls.default_parameters = get_dict_from_init(init, skip=svars)
        cls.default_initial_values = get_dict_from_init(init, include=svars)
    elif svars is None:
        cls.default_parameters = get_dict_from_init(init, include=params)
        cls.default_initial_values = get_dict_from_init(init, skip=params)
    else:
        cls.default_parameters = get_dict_from_init(init, include=params)
        cls.default_initial_values = get_dict_from_init(init, include=svars)
    return cls
