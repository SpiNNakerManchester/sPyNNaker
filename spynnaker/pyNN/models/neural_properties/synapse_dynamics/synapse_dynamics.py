class SynapseDynamics(object):

    def __init__(self, slow=None, fast=None):
        self.fast = fast
        self.slow = slow

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SynapseDynamics)):
            return False
        return (self.slow == other.slow) and (self.fast == other.fast)

    def get_synapse_row_io(self):
        # The slow dynamics dictate the type of synapse row IO to use
        if self.slow is not None:
            # **TODO** fast dynamics header words needs to be taken into account
            assert self.fast is None

            return self.slow.get_synapse_row_io()
        # Otherwise, allow fast to dictate
        else:
            return self.fast.create_synapse_row_io()
