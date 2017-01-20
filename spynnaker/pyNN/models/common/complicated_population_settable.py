from spinn_front_end_common.abstract_models. \
    abstract_requires_rewriting_data_regions_application_vertex import \
    AbstractRequiresRewriteDataRegionsApplicationVertex
from spynnaker.pyNN.models.common.simple_population_settable import \
    SimplePopulationSettable
from abc import abstractmethod


class ComplicatedPopulationSettable(
    SimplePopulationSettable,
    AbstractRequiresRewriteDataRegionsApplicationVertex):
    def __init__(self):
        SimplePopulationSettable.__init__(self)
        AbstractRequiresRewriteDataRegionsApplicationVertex.__init__(self)

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
