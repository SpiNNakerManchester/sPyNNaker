from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod, \
    abstractproperty


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

    @abstractproperty
    def initial_values(self):
        """A dict containing the initial values of the state variables."""

    @abstractmethod
    def get_initial_value(self, variable, selector=None):
        """ gets the value for any variable whose in initialize_parameters.keys

        Should return the current value not the default one

        Must support the variable as listed in initialize_parameters.keys
        but ideally also with _init removed or added

        :param variable: variable name with our without _init
        :type variable:str
        :param selector: a description of the subrange to accept. \
            Or None for all \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py

        :return: A list or an Object which act like a list
        """

    @abstractmethod
    def set_initial_value(self, variable, value, selector=None):
        """ Sets the value for any variable whose in
        initialize_parameters.keys

        Must support the variable as listed in initialize_parameters.keys
        but ideally also with _init removed or added

        :param variable: variable name with our without _init
        :type variable:str
        :param value: New value for the variable
        :param selector: a description of the subrange to accept. \
            Or None for all \
            See: _selector_to_ids in \
            SpiNNUtils.spinn_utilities.ranged.abstract_sized.py

        :return: A list or an Object which act like a list
        """

    @abstractproperty
    def initialize_parameters(self):
        """
        List the parameters that are initializable.

        If "foo" is initializable there should be a setter initialize_foo
        and a getter proporty foo_init

        :return: list of propery names
        """
        # Note: this will have been none_pynn_default_parameters
