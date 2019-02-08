from spynnaker.pyNN.models.neuron.implementations import (
    AbstractStandardNeuronComponent)


class AbstractThresholdType(AbstractStandardNeuronComponent):
    """ Represents types of threshold for a neuron (e.g., stochastic).
    """

    __slots__ = ()
