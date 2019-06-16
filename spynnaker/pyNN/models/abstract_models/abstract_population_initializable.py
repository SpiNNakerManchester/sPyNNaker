from six import add_metaclass
from spinn_utilities.abstract_base import (
    AbstractBase, abstractmethod, abstractproperty)


@add_metaclass(AbstractBase)
class AbstractPopulationInitializable(object):
    """ Indicates that this object has properties that can be initialised by a\
        PyNN Population
    """

    __slots__ = ()

    @abstractmethod
    def initialize(self, variable, value):
        """ Set the initial value of one of the state variables of the neurons\
            in this population.
        """

    @property
    def initial_values(self):
        """ A dict containing the initial values of the state variables.
        """
        return self.get_initial_values(None)

    def get_initial_values(self, selector=None):
        """ A dict containing the initial values of the state variables.

        :param selector: a description of the subrange to accept. \
            Or None for all. \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py
        """
        results = dict()
        for variable_init in self.initialize_parameters:
            if variable_init.endswith("_init"):
                variable = variable_init[:-5]
            else:
                variable = variable_init
            results[variable] = self.get_initial_value(variable_init, selector)
        return results

    @abstractmethod
    def get_initial_value(self, variable, selector=None):
        """ Gets the value for any variable whose in initialize_parameters.keys

        Should return the current value not the default one.

        Must support the variable as listed in initialize_parameters.keys, \
        ideally also with `_init` removed or added.

        :param variable: variable name with our without _init
        :type variable: str
        :param selector: a description of the subrange to accept. \
            Or None for all. \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py
        :return: A list or an Object which act like a list
        """

    @abstractmethod
    def set_initial_value(self, variable, value, selector=None):
        """ Sets the value for any variable whose in \
            initialize_parameters.keys

        Must support the variable as listed in initialize_parameters.keys,\
        ideally also with `_init` removed or added

        :param variable: variable name with our without `_init`
        :type variable: str
        :param value: New value for the variable
        :param selector: a description of the subrange to accept. \
            Or None for all. \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py
        :return: A list or an Object which act like a list
        """

    @abstractproperty
    def initialize_parameters(self):
        """ List the parameters that are initializable.

        If "foo" is initializable there should be a setter initialize_foo \
        and a getter property foo_init

        :return: list of property names
        """
        # Note: this will have been non_pynn_default_parameters
