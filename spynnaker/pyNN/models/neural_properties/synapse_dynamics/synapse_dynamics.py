class SynapseDynamics(object):

    def __init__(self, slow=None, fast=None):
        if fast is not None:
            raise NotImplementedError(
                "Fast synapse dynamics are not currently supported")

        self.fast = fast
        self.slow = slow

    def __eq__(self, other):
        if (other is None) or (not isinstance(other, SynapseDynamics)):
            return False
        return (self.slow == other.slow) and (self.fast == other.fast)

    def get_synapse_row_io(self):
        return self.slow.get_synapse_row_io()

    def get_vertex_executable_suffix(self):
        name = ""
        if self.fast is not None:
           name += self.fast.get_executable_suffix()
           if self.slow is not None:
              name += "_"
        if self.slow is not None: 
           name += self.slow.get_executable_suffix()                       
        return name
    
