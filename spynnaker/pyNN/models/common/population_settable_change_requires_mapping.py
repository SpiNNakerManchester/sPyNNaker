from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable

from spynnaker.pyNN.models.abstract_models.abstract_mappable \
    import AbstractMappable


class PopulationSettableChangeRequiresMapping(
        SimplePopulationSettable, AbstractMappable):
    """ An object all of whose properties can be accessed from a PyNN \
        Population, and which, when changed require mapping to be done again
    """

    def __init__(self):
        AbstractMappable.__init__(self)
        SimplePopulationSettable.__init__(self)
        self._change_requires_mapping = True

    def requires_mapping(self):
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False

    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self._change_requires_mapping = True
