from spynnaker.pyNN import exceptions
from six import add_metaclass
from abc import ABCMeta


@add_metaclass(ABCMeta)
class AbstractContainsUnits(object):
    def __init__(self, units):
        self._units = units

    def units(self, variable):
        if variable in self._units:
            return self._units[variable]
        else:
            raise exceptions.InvalidParameterType(
                "The parameter {} does not exist in this input "
                "conductance component".format(variable))
