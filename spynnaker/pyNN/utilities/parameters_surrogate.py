"""
This class is provided so that the PyNN front-end for PACMAN can successfully
emulate PyNN calls whilst retaining a sane Python class structure.
"""
from spynnaker.pyNN.utilities import utility_calls


class PyNNParametersSurrogate(object):
    """
    Acts so that we can convert the ```dict``` nature of parameters in PyNN
    into the normal Python attributes.  Attempting to get a parameter will
    redirect the request to the appropriate class, attempting to set a 
    parameter will do likewise.

    :param vertex_to_surrogate: The object for which to act as surrogate.
    """
    def __init__(self, vertex_to_surrogate):
        self.vertex = vertex_to_surrogate

    def update(self, updates):
        """Update the parameters with the given values."""
        for (k, v) in updates.iteritems():
            self[k] = v

    def __getitem__(self, key):
        """Will attempt to get the given parameter from the object."""
        # See if the object we're acting as surrogate for has this parameter
        if not hasattr(self.vertex, key):
            raise Exception("Object '%s' does not have parameter '%s'." %
                            (self.vertex, key))

        # Now return the value of that parameter
        return getattr(self.vertex, key)

    def __setitem__(self, key, value):
        # See if the object we're acting as surrogate for has this parameter
        if not hasattr(self.vertex, key):
            raise Exception("Object '%s' does not have parameter '%s'." %
                            (self.vertex, key))
        value = utility_calls.convert_param_to_numpy(value, self.vertex.n_atoms)
        setattr(self.vertex, key, value)
