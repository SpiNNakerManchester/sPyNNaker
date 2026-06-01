# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Decorators to support default argument handling.
"""

import inspect
import logging
from types import MappingProxyType
from typing import (
    Any, Callable, FrozenSet, Iterable, List, Mapping, Optional, Tuple)
from spinn_utilities.classproperty import classproperty
from spinn_utilities.log import FormatAdapter

logger = FormatAdapter(logging.getLogger(__name__))


def _check_args(
        args_to_find: FrozenSet[str], default_args: List[str],
        init_method: Callable) -> None:
    for arg in args_to_find:
        if arg not in default_args:
            raise AttributeError(
                f"Argument {arg} not found, or "
                f"no default value provided in {init_method}")


def get_map_from_init(
        init_method: Callable,
        skip: Optional[FrozenSet[str]] = None,
        include: Optional[FrozenSet[str]] = None) -> Mapping[str, Any]:
    """
    Get an argument initialisation dictionary by examining an
    ``__init__`` method or function.

    :param init_method: The method.
    :param skip: The arguments to be skipped, if any
    :param include: The arguments that must be present, if any
    :return: an initialisation dictionary
    """
    init_args = inspect.getfullargspec(init_method)
    n_defaults = 0 if init_args.defaults is None else len(init_args.defaults)
    n_args = 0 if init_args.args is None else len(init_args.args)
    default_args = ([] if init_args.args is None else
                    init_args.args[n_args - n_defaults:])
    default_values = [] if init_args.defaults is None else init_args.defaults

    # Check that included / skipped things exist
    if include is not None:
        _check_args(include, default_args, init_method)
    if skip is not None:
        _check_args(skip, default_args, init_method)

    as_dict = {arg: value
               for arg, value in zip(default_args, default_values)
               if ((arg != "self") and
                   (skip is None or arg not in skip) and
                   (include is None or arg in include))}
    return MappingProxyType(as_dict)


def default_parameters(parameters: Iterable[str]) -> Callable:
    """
    Specifies arguments which are parameters.  Only works on the
    ``__init__`` method of a class that is additionally decorated with
    :py:meth:`defaults`

    :param parameters:
        The names of the arguments that are parameters
    :returns: A check method to be called when first used
    """
    def wrap(method: Callable) -> Callable:
        # pylint: disable=protected-access
        # Find the real method in case we use multiple of these decorators
        wrapped = method
        while hasattr(method, "_method"):
            method = getattr(method, "_method")

        # Set the parameters of the method to be used later
        method._parameters = (  # type: ignore[attr-defined]
            frozenset(parameters))
        method_args = inspect.getfullargspec(method)

        def wrapper(*args: Any, **kwargs: Any) -> None:
            # Check for state variables that have been specified in cell_params
            args_provided = method_args.args[:len(args)]
            args_provided.extend([
                arg for arg in kwargs if arg in method_args.args])
            parameters = method._parameters  # type: ignore[attr-defined]
            for arg in args_provided:
                if arg not in parameters and arg != "self":
                    logger.warning(
                        "Formal PyNN specifies that {} should be set using "
                        "initial_values not cell_params", arg)
            wrapped(*args, **kwargs)

        # Store the real method in the returned object
        wrapper._method = method  # type: ignore[attr-defined]
        return wrapper
    return wrap


def default_initial_values(state_variables: Iterable[str]) -> Callable:
    """
    Specifies arguments which are state variables.  Only works on the
    ``__init__`` method of a class that is additionally decorated with
    :py:meth:`defaults`

    :param state_variables:
        The names of the arguments that are state variables
    :returns: A check method to be called when first used
    """
    def wrap(method: Callable) -> Callable:
        """
        Wraps the init method with a check method

        :param method: init method to wrap
        :returns: A check method to be called when first used
        """
        # pylint: disable=protected-access
        # Find the real method in case we use multiple of these decorators
        wrapped = method
        while hasattr(method, "_method"):
            method = getattr(method, "_method")

        # Store the state variables of the method to be used later
        method._state_variables = (  # type: ignore[attr-defined]
            frozenset(state_variables))
        method_args = inspect.getfullargspec(method)

        def wrapper(*args: Any, **kwargs: Any) -> None:
            # Check for state variables that have been specified in cell_params
            args_provided = method_args.args[:len(args)]
            args_provided.extend([
                arg for arg in kwargs if arg in method_args.args])
            variables = method._state_variables  # type: ignore[attr-defined]
            for arg in args_provided:
                if arg in variables:
                    logger.warning(
                        "Formal PyNN specifies that {} should be set using "
                        "initial_values not cell_params", arg)
            wrapped(*args, **kwargs)

        # Store the real method in the returned object
        wrapper._method = method  # type: ignore[attr-defined]
        return wrapper
    return wrap


def defaults(cls: type) -> type:
    """
    Deprecated! Extend AbstractProvidesDefaults instead

    Get the default parameters and state variables from the arguments to
    the ``__init__`` method.  This uses the decorators
    :py:func:`default_parameters` and :py:func:`default_initial_values` to
    determine the parameters and state variables respectively.
    If only one is specified, the other is assumed to be the remaining
    arguments.
    If neither are specified, it is assumed that all default arguments are
    parameters.

    :returns: input unchanged
    """
    logger.warning("@defaults is deprecated! "
                   "Extend AbstractProvidesDefaults instead")
    if not inspect.isclass(cls):
        raise TypeError(f"{cls} is not a class")
    if not hasattr(cls, "__init__"):
        raise AttributeError(f"No __init__ found in {cls}")
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
        cls.default_parameters = get_map_from_init(init)
        cls.default_initial_values = {}
    elif params is None:
        cls.default_parameters = get_map_from_init(init, skip=svars)
        cls.default_initial_values = get_map_from_init(init, include=svars)
    elif svars is None:
        cls.default_parameters = get_map_from_init(init, include=params)
        cls.default_initial_values = get_map_from_init(init, skip=params)
    else:
        cls.default_parameters = get_map_from_init(init, include=params)
        cls.default_initial_values = get_map_from_init(init, include=svars)
    return cls


class AbstractProvidesDefaults(object):
    """
    Provides the default_parameters and default_initial_values properties

    These will be filled in based on the @default_parameters and
    @default_initial_values decorators with values read from the init.
    """

    __cashed_defaults: Optional[Mapping[str, Any]] = None
    __cashed_initials: Optional[Mapping[str, Any]] = None

    @classmethod
    def __fill_in_defaults(cls) -> None:
        """
        Fills in default_parameters and default_initial_values attributes
        """
        # get the init method
        init = getattr(cls, "__init__")
        # Find the real method as there may be decorators
        while hasattr(init, "_method"):
            init = getattr(init, "_method")

        # read the values from the init method
        init_args = inspect.getfullargspec(init)
        n_defaults = 0 if init_args.defaults is None else len(
            init_args.defaults)
        n_args = 0 if init_args.args is None else len(init_args.args)
        default_args = ([] if init_args.args is None else
                        init_args.args[n_args - n_defaults:])
        if init_args.defaults is None:
            default_values: Tuple = ()
        else:
            default_values = init_args.defaults

        # get the keys based on the decorators
        if hasattr(init, "_parameters"):
            params = getattr(init, "_parameters")
            if hasattr(init, "_state_variables"):
                svars = getattr(init, "_state_variables")
                assert len(params.intersection(svars)) == 0
            else:
                svars = frozenset(svar for svar in default_args
                                  if svar not in params)
        else:
            if hasattr(init, "_state_variables"):
                svars = getattr(init, "_state_variables")
                params = frozenset(param for param in default_args
                                   if param not in svars)
            else:
                svars = frozenset()
                params = set(default_args)

        # Check all decorator values used
        _check_args(params.union(svars), default_args, init)

        # fill in the defaults so this method is only called once
        __defaults = {}
        __initials = {}
        for arg, value in zip(default_args, default_values):
            if arg in params:
                __defaults[arg] = value
            elif arg in svars:
                __initials[arg] = value
        cls.__cashed_defaults = MappingProxyType(__defaults)
        cls.__cashed_initials = MappingProxyType(__initials)

    @classproperty
    def default_parameters(  # pylint: disable=no-self-argument
            cls) -> Mapping[str, Any]:
        """
        Get the default values for the parameters of the model.

        If a @default_parameters decorator is used
        this will be the init default values for those keys

        If no @default_parameters decorator is used
        this will be all the init parameters with a default value
        less any defined in @default_initial_values

        :returns: Mapping of parameter names to default values
        """
        if cls.__cashed_defaults is None:
            cls.__fill_in_defaults()
            assert cls.__cashed_defaults is not None
        return cls.__cashed_defaults

    @classproperty
    def default_initial_values(  # pylint: disable=no-self-argument
            cls) -> Mapping[str, Any]:
        """
        Get the default initial values for the state variables of the model.

        If @default_initial_values decorator is used
        this will be the init default values for those keys

        If no @default_initial_values decorator is used
        but a @default_parameters decorator was used
        this will be all the init parameters with a default value
        less any defined in @default_parameters

        If neither decorator is used this will be an empty Mapping

        :returns:
            The default initial values for the state variables of the model.

        """
        if cls.__cashed_initials is None:
            cls.__fill_in_defaults()
            assert cls.__cashed_initials is not None
        return cls.__cashed_initials
