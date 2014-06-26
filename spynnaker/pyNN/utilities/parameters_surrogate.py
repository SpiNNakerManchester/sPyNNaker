"""
This class is provided so that the PyNN front-end for PACMAN can succesfully
emulate PyNN calls whilst retaining a sane Python class structure.
"""


class PyNNParametersSurrogate(object):
    """
    Acts so that we can convert the ```dict``` nature of parameters in PyNN
    into the normal Python attributes.  Attempting to get a parameter will
    redirect the request to the appropriate class, attempting to set a 
    parameter will do likewise.

    :param obj: The object for which to act as surrogate.
    """
    def __init__(self, obj):
        self._obj = obj

    def update(self, updates):
        """Update the parameters with the given values."""
        for (k, v) in updates.iteritems():
            self[k] = v

    def __getitem__( self, key ):
        """Will attempt to get the given parameter from the object."""
        # See if the object we're acting as surrogate for has this parameter
        if not hasattr(self._obj, key):
            raise Exception("Object '%s' does not have parameter '%s'." %
                            (self._obj, key))

        # Now return the value of that parameter
        return getattr(self._obj, key)

    def __setitem__(self, key, value):
        # See if the object we're acting as surrogate for has this parameter
        if not hasattr(self._obj, key):
            raise Exception("Object '%s' does not have parameter '%s'." %
                            (self._obj, key))
        value = self._obj.convert_param(value,  self._obj.atoms)
        setattr(self._obj, key, value)
