import math
import numpy


class DelayBlock(object):
    """ A block of delays for a subvertex
    """

    def __init__(
            self, n_delay_stages, delay_per_stage, vertex_slice):

        self._delay_per_stage = delay_per_stage
        self._n_delay_stages = n_delay_stages
        n_words_per_row = int(math.ceil(vertex_slice.n_atoms / 32.0))
        self._delay_block = numpy.zeros(
            (n_delay_stages, n_words_per_row), dtype="uint32")

    def add_delay(self, source_id, stage):
        word_id = int(source_id / 32.0)
        bit_id = source_id - (word_id * 32)
        self._delay_block[stage - 1][word_id] |= (1 << bit_id)

    @property
    def delay_block(self):
        return self._delay_block
