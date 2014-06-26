__author__ = 'stokesa6'

from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector
from spynnaker.pyNN import exceptions


class DistanceDependentProbabilityConnector(AbstractConnector):

    def __init__(self):
        raise exceptions.SpynnakerException("This connector is currently not "
                                            "supported by the tool chain....."
                                            "watch this space")