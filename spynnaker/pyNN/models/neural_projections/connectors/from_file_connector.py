from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from .from_list_connector import FromListConnector
import os
import numpy
from six import add_metaclass


@add_metaclass(AbstractBase)
class FromFileConnector(FromListConnector):

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, verbose=False):
        self._file = file

        real_file = file
        opened_file = False
        if isinstance(file, basestring):
            real_file = self.get_reader(file)
            opened_file = True

        if distributed:
            directory = os.path.dirname(real_file.file)
            filename = "{}.".format(os.path.basename(real_file.file))

            conns = list()
            for found_file in os.listdir(directory):
                if found_file.startswith(filename):
                    file_reader = self.get_reader(found_file)
                    conns.append(file_reader.read())
                    file_reader.close()
            conn_list = numpy.concatenate(conns)
        else:
            conn_list = real_file.read()

        if opened_file:
            real_file.close()

        FromListConnector.__init__(self, conn_list, safe, verbose)

    def __repr__(self):
        return "FromFileConnector({})".format(self._file)

    @abstractmethod
    def get_reader(self, file):  # @ReservedAssignment
        """
        get a filereader object probably using the pynn methods

        For example calling
        from pyNN.recording import files
        return files.StandardTextFile(file, mode="r")
        :return: A pynn StandardTextFile or similar
        """
