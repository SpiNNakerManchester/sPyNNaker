from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm


class KeySpaceTracker(ElementAllocatorAlgorithm):

    def __init__(self):
        super(KeySpaceTracker, self).__init__(0, (2**32 - 1))

    def allocate_keys(self, r_info):
        """ Allocate all the keys in the routing information
            NOTE assumes masks are all 1s followed by all 0s
        """
        for key_and_mask in r_info.keys_and_masks:
            key = key_and_mask.key
            mask = key_and_mask.mask
            n_keys = 2 ** self.count_trailing_0s(mask)
            self._allocate_elements(key, n_keys)

    def is_allocated(self, key, mask):
        """ Determine if any of the keys in the mask are allocated
            NOTE assumes mask is all 1s followed by all 0s
        """
        index = self._find_slot(key)
        if index is None:
            return True
        n_keys = 2 ** self.count_trailing_0s(mask)
        space = self._check_allocation(index, key, n_keys)
        return space is None

    @staticmethod
    def count_trailing_0s(mask):
        """ Count bitwise zeros at the LSB end of a number
            NOTE assumes a 32-bit number
        """
        for i in range(32):
            if mask & (1 << i):
                return i
        return 32
