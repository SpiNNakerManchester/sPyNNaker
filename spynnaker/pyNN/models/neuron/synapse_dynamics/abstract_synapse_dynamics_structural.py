from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics import AbstractSynapseDynamics

from six import add_metaclass
from abc import ABCMeta
from abc import abstractmethod

@add_metaclass(ABCMeta)
class AbstractSynapseDynamicsStructural(AbstractSynapseDynamics):

    def __init__(self):
        AbstractSynapseDynamics.__init__(self)