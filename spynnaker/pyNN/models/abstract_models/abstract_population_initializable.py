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
    def initialize_parameters(self):
        """
        List the parameters that are initializable.

        If "foo" is initializable there should be a setter initialize_foo
        and a getter proporty foo_init

        :return: list of propery names
        """
        # Note: this will have been none_pynn_default_parameters
