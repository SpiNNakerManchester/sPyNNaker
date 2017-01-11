from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from spinn_front_end_common.abstract_models. \
    abstract_requires_rewriting_data_regions_application_vertex import \
    AbstractRequiresRewriteDataRegionsApplicationVertex


@add_metaclass(ABCMeta)
class AbstractPopulationSettableApplicationVertex(
        AbstractRequiresRewriteDataRegionsApplicationVertex):
    """ Indicates that some properties of this object can be accessed from\
        the PyNN population set and get methods
    """

    @abstractmethod
    def get_value(self, key):
        """ Get a property
        """

    @abstractmethod
    def set_value(self, key, value):
        """ Set a property

        :param key: the name of the parameter to change
        :param value: the new value of the parameter to assign
        """

    @abstractmethod
    def read_neuron_parameters_from_machine(
            self, transceiver, placement, vertex_slice):
        """ extracts the data from the neuron parameter region

        :param transceiver: the SpinnMan interface
        :param placement: the placement object for a vertex
        :param vertex_slice: the slice of atoms for this vertex
        :return: the ByteArray containing the data from sdram of the neuron
        parameter region
        """
