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
from spynnaker.pyNN.models.recorder import Recorder as _BaseClass
logger = FormatAdapter(logging.getLogger(__name__))


class Recorder(_BaseClass):
    """
    .. deprecated:: 6.0
        Use :py:class:`spynnaker.pyNN.models.recorder.Recorder` instead.
    """
    # DO NOT DEFINE SLOTS! Multiple inheritance problems otherwise.
    # __slots__ = []

    def __init__(self, population):
        """
        :param population: the population to record for
        :type population: ~spynnaker.pyNN.models.populations.Population
        """
        super(Recorder, self).__init__(population)
        logger.warning(
            "please use spynnaker.pyNN.models.recorder.Recorder instead")
