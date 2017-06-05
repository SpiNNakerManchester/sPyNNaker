from spynnaker.pyNN.models.neuron.synapse_dynamics.abstract_synapse_dynamics import AbstractSynapseDynamics

from six import add_metaclass

from spinn_utilities.abstract_base import AbstractBase, abstractmethod

@add_metaclass(AbstractBase)
class AbstractSynapseDynamicsStructural(AbstractSynapseDynamics):

    def __init__(self):
        AbstractSynapseDynamics.__init__(self)