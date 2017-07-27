from six import add_metaclass

from spinn_utilities.abstract_base import \
    AbstractBase, abstractmethod, abstractproperty


@add_metaclass(AbstractBase)
class AbstractWeightDependence(object):

    __slots__ = ()

    def __init__(self):
        pass

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get any provenance data

        :param pre_population_label: label of pre.
        :param post_population_label:label of post.
        :return the provenance data of the weight dependency
        """
        return list()

    @abstractmethod
    def get_parameter_names(self):
        """ returns iterable of parameter names as basestrings

        :return: iterable of basestring
        """

    @abstractmethod
    def is_same_as(self, weight_dependence):
        """ Determine if this weight dependence is the same as another
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(
            self, n_synapse_types, n_weight_terms):
        """ Get the amount of SDRAM used by the parameters of this rule
        """

    @abstractmethod
    def write_parameters(
            self, spec, machine_time_step, weight_scales, n_weight_terms):
        """ Write the parameters of the rule to the spec
        """

    @abstractproperty
    def weight_maximum(self):
        """ The maximum weight that will ever be set in a synapse as a result\
            of this rule
        """
