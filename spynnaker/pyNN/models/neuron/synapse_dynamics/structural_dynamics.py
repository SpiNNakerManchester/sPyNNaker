from .pynn_synapse_dynamics import PyNNSynapseDynamics


class StructuralDynamics(PyNNSynapseDynamics):
    __slots__ = ["__structure"]

    def __init__(self, slow=None, fast=None, structure=None):
        super(StructuralDynamics, self).__init__(slow=slow, fast=fast)
        self.__structure = structure

    @property
    def structure(self):
        return self.__structure
