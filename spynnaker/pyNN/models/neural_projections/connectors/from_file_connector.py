# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Union

import numpy
from numpy.typing import NDArray

from pyNN.recording.files import BaseFile, StandardTextFile

from .from_list_connector import FromListConnector


class FromFileConnector(FromListConnector):
    """
    Make connections according to a list read from a file.
    """
    __slots__ = ("_file", )

    def __init__(
            self, file: Union[str, BaseFile],  # @ReservedAssignment
            distributed=False, safe=True, callback=None, verbose=False):
        """
        :param str file:
            Either an open file object or the filename of a file containing a
            list of connections, in the format required by
            :py:class:`FromListConnector`.
            Column headers, if included in the file, must be specified using
            a list or tuple, e.g.::

                # columns = ["i", "j", "weight", "delay", "U", "tau_rec"]

            .. note::
                The header requires `#` at the beginning of the line.
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

    def _read_conn_list(
            self, the_file: BaseFile, distributed: bool) -> NDArray:
        if not distributed:
            return the_file.read()
        filename = f"{os.path.basename(the_file.file)}."

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
        return f"FromFileConnector({self._file})"

    def get_reader(self, file: str) -> BaseFile:  # @ReservedAssignment
        """
        Get a file reader object using the PyNN methods.

        :return: A pynn StandardTextFile or similar
        :rtype: ~pyNN.recording.files.StandardTextFile
        """
        return StandardTextFile(file, mode="r")
