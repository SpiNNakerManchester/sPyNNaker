# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from pacman.utilities.algorithm_utilities import ElementAllocatorAlgorithm
from pacman.utilities.constants import FULL_MASK, BITS_IN_KEY


class KeySpaceTracker(ElementAllocatorAlgorithm):
    """ Tracks keys used to determine key overlap
    """

    def __init__(self):
        super().__init__(0, FULL_MASK)

    def allocate_keys(self, r_info):
        """ Allocate all the keys in the routing information
            NOTE assumes masks are all 1s followed by all 0s

        :param PartitionRoutingInfo r_info: The routing information to add
        """
        for key_and_mask in r_info.keys_and_masks:
            key = key_and_mask.key
            mask = key_and_mask.mask
            n_keys = 2 ** self.count_trailing_0s(mask)
            self._allocate_elements(key, n_keys)

    def is_allocated(self, key, n_keys):
        """ Determine if any of the keys in the mask are allocated
            NOTE assumes mask is all 1s followed by all 0s

        :param int key: The key at the start of the allocation
        :param int n_keys: The number of keys to check
        :rtype: bool
        """
        index = self._find_slot(key)
        if index is None:
            return True
        space = self._check_allocation(index, key, n_keys)
        return space is None

    @staticmethod
    def count_trailing_0s(mask):
        """ Count bitwise zeros at the LSB end of a number
            NOTE assumes a 32-bit number

        :param mask: The mask to be checked
        """
        for i in range(BITS_IN_KEY):
            if mask & (1 << i):
                return i
        return 32
