import numpy

try:
    from pyNN.random import RandomDistribution
except ImportError:
    RandomDistribution = None


def generateParameter(paramInfo, paramIndex=0):
    """Return a parameter value, given the parameter info, which may be a
    constant, list or distribution.
    """
    # Currently assume hard-coded value:
    if isinstance(paramInfo, (int, float)):
        return paramInfo
    elif RandomDistribution is not None and isinstance(paramInfo,
                                                       RandomDistribution):
        return paramInfo.next(n=1)
    elif isinstance(paramInfo, list):
        if paramIndex >= 0 and paramIndex < len(paramInfo):
            return paramInfo[paramIndex]
        else:
            raise Exception("Invalid index in list parameter requested!")
    else:
        raise TypeError(
            "ERROR: generateParameter - The format of this parameter info"
            " is not supported."
        )


def generateParameterArray(paramInfo, n_present, paramIndices=None):
    """
    Returns an array of parameter values for a given parameter info
    """
    if isinstance(paramInfo, (int, float)):
        return numpy.array([paramInfo] * n_present)
    elif isinstance(paramInfo, list):
        return numpy.extract(paramIndices, numpy.asarray(paramInfo))
    elif isinstance(paramInfo, RandomDistribution):
        return numpy.asarray(paramInfo.next(n=n_present))
