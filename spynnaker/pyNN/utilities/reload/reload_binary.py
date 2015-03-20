import os


class ReloadBinary(object):
    """ A binary to be reloaded
    """

    def __init__(self, binary_path, core_subsets):
        self._binary_path = binary_path
        self._core_subsets = core_subsets
        self._binary_size = os.stat(binary_path).st_size

    @property
    def binary_path(self):
        return self._binary_path

    @property
    def core_subsets(self):
        return self._core_subsets

    @property
    def binary_size(self):
        return self._binary_size
