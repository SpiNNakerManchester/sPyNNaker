class PyNNSynapseDynamics(object):
    __slots__ = ["_slow"]

    def __init__(self, slow=None, fast=None):
        if fast is not None:
            raise NotImplementedError(
                "Fast synapse dynamics are not currently supported")

        self._slow = slow

    @property
    def slow(self):
        return self._slow
