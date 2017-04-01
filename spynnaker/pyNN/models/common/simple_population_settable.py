from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable


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
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise Exception("Parameter {} not found".format(key))
