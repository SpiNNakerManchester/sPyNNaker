from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN import exceptions


class DistanceDependentProbabilityConnector(AbstractConnector):

    def generate_synapse_list(self, prevertex, postvertex, delay_scale,
                              synapse_type):
        raise exceptions.SpynnakerException("This connector is currently not "
                                            "supported by the tool chain....."
                                            "watch this space")

    def __init__(self):
        raise exceptions.SpynnakerException("This connector is currently not "
                                            "supported by the tool chain....."
                                            "watch this space")