from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractPopulationSettable


class SimplePopulationSettable(AbstractPopulationSettable):
    """ An object all of whose properties can be accessed from a PyNN\
        Population i.e. no properties are hidden
    """

    __slots__ = ()

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise Exception("Population {} does not have parameter {}".format(
            self, key))

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        if not hasattr(self, key):
            raise Exception("Parameter {} not found".format(key))
        setattr(self, key, value)
