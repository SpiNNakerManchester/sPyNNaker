from spynnaker.pyNN.models.abstract_models.abstract_population_settable \
    import AbstractPopulationSettable


class SimplePopulationSettable(AbstractPopulationSettable):
    """ An object all of whose properties can be accessed from a PyNN\
        Population i.e. no properties are hidden
    """

    def __init__(self):
        AbstractPopulationSettable.__init__(self)
        self._parameters_have_changed = False

    def parameters_have_changed(self):
        return self._parameters_have_changed

    def mark_parameters_unchanged(self):
        self._parameters_have_changed = False

    def get_value(self, key):
        """ Get a property of the overall model
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise Exception("Population {} does not have parameter {}".format(
            self, key))

    def set_value(self, key, value):
        """ Set a property of the overall model

        :param key: the name of the param to change
        :param value: the value of the parameter to change
        """
        if hasattr(self, key) and getattr(self, key) != value:
            setattr(self, key, value)
            self._parameters_have_changed = True
        else:
            raise Exception("Type {} does not have parameter {}"
                            .format(self._model_name, key))
