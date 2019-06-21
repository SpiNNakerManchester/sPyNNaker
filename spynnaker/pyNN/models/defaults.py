import inspect
try:
    from inspect import getfullargspec
except ImportError:
    # Python 2.7 hack
    from inspect import getargspec as getfullargspec


def _check_args(args_to_find, default_args, init):
    for arg in args_to_find:
        if arg not in default_args:
            raise AttributeError(
                "Argument {} not found, or no default value provided in {}"
                .format(arg, init))


def get_dict_from_init(init, skip=None, include=None):
    init_args = getfullargspec(init)
    n_defaults = len(init_args.defaults)
    n_args = len(init_args.args)
    default_args = init_args.args[n_args - n_defaults:]
    default_values = init_args.defaults

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
    """ Specifies arguments which are parameters.  Only works on the __init__\
        method of a class that is additionally decorated with\
        :py:meth:`defaults``

    :param parameters: The names of the arguments that are parameters
    :type parameters: set of str
    """
    def wrap(method):
        method._parameters = parameters
        return method
    return wrap


def default_initial_values(state_variables):
    """ Specifies arguments which are state variables.  Only works on the\
        __init__ method of a class that is additionally decorated with\
        :py:meth:`defaults``

    :param state_variables: The names of the arguments that are state variables
    :type state_variables: set of str
    """
    def wrap(method):
        method._state_variables = state_variables
        return method
    return wrap


def defaults(cls):
    """ Get the default parameters and state variables from the arguments to\
        the __init__ method.  This uses the decorators\
        :py:func:`default_parameters` and :py:func:`default_initial_values` to\
        determine the parameters and state variables respectively.\
        If only one is specified, the other is assumed to be the remaining\
        arguments.\
        If neither are specified, it is assumed that all default arguments are\
        parameters.
    """
    if not inspect.isclass(cls):
        raise Exception("{} is not a class".format(cls))
    if not hasattr(cls, "__init__"):
        raise AttributeError("No __init__ found in {}".format(cls))
    init = getattr(cls, "__init__")
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
