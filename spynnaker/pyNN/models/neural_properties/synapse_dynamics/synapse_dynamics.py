class SynapseDynamics(object):

    def __init__(self, slow=None, fast=None):
        if fast is not None:
            raise NotImplementedError(
                "Fast synapse dynamics are not currently supported")

        self.fast = fast
        self.slow = slow

    @property
    def weight_scale(self):
        return self.slow.weight_scale

    @weight_scale.setter
    def weight_scale(self, weight_scale):
        self.slow.weight_scale = weight_scale

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SynapseDynamics)):
            return False
        return (self.slow == other.slow) and (self.fast == other.fast)

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_synapse_row_io(self):
        return self.slow.get_synapse_row_io()
