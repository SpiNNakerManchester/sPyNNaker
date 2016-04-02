from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty


@add_metaclass(ABCMeta)
class AbstractTimingDependence(object):

    @abstractmethod
    def is_same_as(self, timing_dependence):
        """ Determine if this timing dependence is the same as another
        """

    @abstractproperty
    def vertex_executable_suffix(self):
        """ The suffix to be appended to the vertex executable for this rule
        """

    @abstractproperty
    def pre_trace_n_bytes(self):
        """ The number of bytes used by the pre-trace of the rule per neuron
        """

    @abstractmethod
    def get_parameters_sdram_usage_in_bytes(self):
        """ Get the amount of SDRAM used by the parameters of this rule
        """

    @abstractproperty
    def n_weight_terms(self):
        """ The number of weight terms expected by this timing rule
        """

    @abstractmethod
    def write_parameters(self, spec, machine_time_step, weight_scales):
        """ Write the parameters of the rule to the spec
        """

    @abstractproperty
    def synaptic_structure(self):
        """ Get the synaptic structure of the plastic part of the rows
        """

    def get_provenance_data(self, pre_population_label, post_population_label):
        """ Get any provenance data
        """
        return list()
