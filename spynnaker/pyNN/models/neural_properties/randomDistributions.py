import numpy

try:
    from pyNN.random import RandomDistribution
except ImportError:
    RandomDistribution = None


def generate_parameter(param_info, param_index=0):
    """Return a parameter value, given the parameter info, which may be a
    constant, list or distribution.
    """
    # Currently assume hard-coded value:
    if isinstance(param_info, (int, float)):
        return param_info
    elif RandomDistribution is not None and isinstance(param_info,
                                                       RandomDistribution):
        val = param_info.next(n=1)
        if hasattr(val, "__len__"):
            return val[0]
        return val
    elif isinstance(param_info, list):
        if 0 <= param_index < len(param_info):
            return param_info[param_index]
        else:
            raise Exception("Invalid index in list parameter requested!")
    else:
        raise TypeError(
            "ERROR: generateParameter - The format of this parameter info"
            " is not supported."
        )


def generate_parameter_array(param_info, n_present, param_indices=None):
    """
    Returns an array of parameter values for a given parameter info
    """
    if isinstance(param_info, (int, float)):
        return numpy.array([param_info] * n_present)
    elif isinstance(param_info, list):
        return numpy.extract(param_indices, numpy.asarray(param_info))
    elif isinstance(param_info, RandomDistribution):
        if n_present > 0:
            vals = param_info.next(n=n_present)
            if not hasattr(vals, "__len__"):
                return numpy.array([vals])
            return vals
        else:
            return numpy.zeros(0)
