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

import logging
from spinn_utilities.log import FormatAdapter
from spinn_front_end_common.data import FecDataWriter
from .spynnaker_data_view import SpynnakerDataView

logger = FormatAdapter(logging.getLogger(__name__))


class SpynnakerDataWriter(FecDataWriter, SpynnakerDataView):
    """
    Writer class for the Spy Data building one the Fec writer

    """

    def setup(self):
        FecDataWriter.setup(self)
        self._spy_data._SpynnakerDataModel__clear()

    def set_min_delay(self, min_delay):
        """
        Sets a min delay or accepts None to use machine_time_step

        :param min_delay: new value or None to say use machine_time_step
        :type min_delay: int or None
        :return:
        """
        self._spy_data._SpynnakerDataModel__min_delay = min_delay
