

class BitFieldData(object):

    def __init__(self, processor_id, bit_field, master_pop_key):
        self._processor_id = processor_id
        self._bit_field = bit_field
        self._master_pop_key = master_pop_key

    @property
    def processor_id(self):
        return self._processor_id

    @property
    def bit_field(self):
        return self._bit_field

    @property
    def master_pop_key(self):
        return self._master_pop_key
