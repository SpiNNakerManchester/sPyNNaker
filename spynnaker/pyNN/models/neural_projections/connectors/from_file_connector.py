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

import os
import numpy
from pyNN.recording.files import StandardTextFile
from .from_list_connector import FromListConnector


class FromFileConnector(FromListConnector):
    """ Make connections according to a list read from a file.
    """
    # pylint: disable=redefined-builtin
    __slots__ = ["_file"]

    def __init__(
            self, file,  # @ReservedAssignment
            distributed=False, safe=True, callback=None, verbose=False):
        """
        :param str file:
            Either an open file object or the filename of a file containing a
            list of connections, in the format required by
            :py:class:`FromListConnector`.
            Column headers, if included in the file, must be specified using
            a list or tuple, e.g.::

                # columns = ["i", "j", "weight", "delay", "U", "tau_rec"]

            Note that the header requires `#` at the beginning of the line.
        :type file: str or ~io.FileIO
        :param bool distributed:
            Basic pyNN says:

                if this is ``True``, then each node will read connections from
                a file called ``filename.x``, where ``x`` is the MPI rank. This
                speeds up loading connections for distributed simulations.

            .. note::
                Always leave this as ``False`` with sPyNNaker, which is not
                MPI-based.
        :param bool safe:
            Whether to check that weights and delays have valid values.
            If ``False``, this check is skipped.
        :param callable callback:
            if given, a callable that display a progress bar on the terminal.

            .. note::
                Not supported by sPyNNaker.
        :param bool verbose:
            Whether to output extra information about the connectivity to a
            CSV file
        """
        self._file = file
        if isinstance(file, str):
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
        super().__init__(
            conn_list, safe=safe, verbose=verbose,
            column_names=column_names, callback=callback)

    def _read_conn_list(self, the_file, distributed):
        if not distributed:
            return the_file.read()
        filename = "{}.".format(os.path.basename(the_file.file))

        # This assumes it finds the files in the right order!
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
        :rtype: ~pynn.recording.files.StandardTextFile
        """
        return StandardTextFile(file, mode="r")
