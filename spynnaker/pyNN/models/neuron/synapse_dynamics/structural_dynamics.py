from .pynn_synapse_dynamics import PyNNSynapseDynamics


class StructuralDynamics(PyNNSynapseDynamics):
    def __init__(self, slow=None, fast=None, structure=None):
        super(StructuralDynamics, self).__init__(slow=slow, fast=fast)
        self._structure = structure

    @property
    def structure(self):
        return self._structure
