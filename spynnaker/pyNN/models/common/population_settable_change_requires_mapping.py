from spynnaker.pyNN.models.common.simple_population_settable \
    import SimplePopulationSettable

from spinn_front_end_common.interface.abstract_mappable_interface \
    import AbstractMappableInterface


class PopulationSettableChangeRequiresMapping(
        SimplePopulationSettable, AbstractMappableInterface):
    """ An object all of whose properties can be accessed from a PyNN \
        Population, and which, when changed require mapping to be done again
    """

    def __init__(self):
        AbstractMappableInterface.__init__(self)
        SimplePopulationSettable.__init__(self)
        self._change_requires_mapping = True

    def requires_mapping(self):
        return self._change_requires_mapping

    def mark_no_changes(self):
        self._change_requires_mapping = False

    def set_value(self, key, value):
        SimplePopulationSettable.set_value(self, key, value)
        self._change_requires_mapping = True
