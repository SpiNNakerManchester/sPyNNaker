from spynnaker.pyNN.models.neuron.implementations\
    import AbstractStandardNeuronComponent


class AbstractAdditionalInput(AbstractStandardNeuronComponent):
    """ Marker for a possible additional independent input for a model
    """

    __slots__ = ()
