from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from .from_list_connector import FromListConnector
import os
import numpy
from six import add_metaclass


@add_metaclass(AbstractBase)
class FromFileConnector(FromListConnector):
    # pylint: disable=redefined-builtin
    __slots__ = ["_file"]

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, verbose=False):
        self._file = file
        if isinstance(file, basestring):
            real_file = self.get_reader(file)
            try:
                conn_list = self._read_conn_list(real_file, distributed)
            finally:
                real_file.close()
        else:
            conn_list = self._read_conn_list(file, distributed)
        super(FromFileConnector, self).__init__(conn_list, safe, verbose)

    def _read_conn_list(self, the_file, distributed):
        if not distributed:
            return the_file.read()
        filename = "{}.".format(os.path.basename(the_file.file))

        conns = list()
        for found_file in os.listdir(os.path.dirname(the_file.file)):
            if found_file.startswith(filename):
                file_reader = self.get_reader(found_file)
                try:
                    conns.append(file_reader.read())
                finally:
                    file_reader.close()
        return numpy.concatenate(conns)

    def __repr__(self):
        return "FromFileConnector({})".format(self._file)

    @abstractmethod
    def get_reader(self, file):  # @ReservedAssignment
        """ Get a filereader object, probably using the pynn methods.

        For example calling:

        from pyNN.recording import files
        return files.StandardTextFile(file, mode="r")

        :return: A pynn StandardTextFile or similar
        """
