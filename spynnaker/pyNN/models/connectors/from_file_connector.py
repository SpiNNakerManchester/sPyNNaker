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

from .from_list_connector import FromListConnector
import os
import numpy
from six import string_types
from pyNN.connectors import FromFileConnector as PyNNFromFileConnector
from pyNN.recording import files


class FromFileConnector(FromListConnector, PyNNFromFileConnector):
    # pylint: disable=redefined-builtin
    __slots__ = ["_file"]

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, callback=None, verbose=False):
        self._file = file
        if isinstance(file, string_types):
            real_file = self.get_reader(file)
            try:
                conn_list = self._read_conn_list(real_file, distributed)
            finally:
                real_file.close()
        else:
            conn_list = self._read_conn_list(file, distributed)

        column_names = self.get_reader(self._file).get_metadata().get(
            'columns')
        if column_names is not None:
            column_names = [column for column in column_names
                            if column not in ("i", "j")]

        # pylint: disable=too-many-arguments
        FromListConnector.__init__(
            self, conn_list, safe=safe, verbose=verbose,
            column_names=column_names, callback=callback)
        PyNNFromFileConnector.__init__(
            self, file=file, distributed=distributed, safe=safe,
            callback=callback)

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

    def get_reader(self, file):  # @ReservedAssignment
        """ Get a file reader object using the PyNN methods.

        :return: A pynn StandardTextFile or similar
        """
        return files.StandardTextFile(file, mode="r")
