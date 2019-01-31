import math
import numpy


class DelayBlock(object):
    """ A block of delays for a vertex.
    """
    __slots__ = [
        "__delay_block",
        "__delay_per_stage",
        "__n_delay_stages"]

    def __init__(
            self, n_delay_stages, delay_per_stage, vertex_slice):
        self.__delay_per_stage = delay_per_stage
        self.__n_delay_stages = n_delay_stages
        n_words_per_row = int(math.ceil(vertex_slice.n_atoms / 32.0))
        self.__delay_block = numpy.zeros(
            (n_delay_stages, n_words_per_row), dtype="uint32")

    def add_delay(self, source_id, stage):
        word_id = int(source_id / 32.0)
        bit_id = int(source_id - (word_id * 32))
        self.__delay_block[int(stage - 1)][word_id] |= (1 << bit_id)

    @property
    def delay_block(self):
        return self.__delay_block
