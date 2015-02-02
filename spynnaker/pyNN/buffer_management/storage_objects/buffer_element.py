from spynnaker.pyNN import exceptions


class BufferElement(object):

    def __init__(self, entry):
        self._entry = entry
        self._seqeuence_no = None

    @property
    def entry(self):
        return self._entry

    @property
    def seqeuence_no(self):
        return self._seqeuence_no

    def set_seqeuence_no(self, new_value):
        if self._seqeuence_no is not None:
            raise exceptions.ConfigurationException(
                "Tried to set a sequence number which had already been set. "
                "Please correct and try again")
        self._seqeuence_no = new_value
