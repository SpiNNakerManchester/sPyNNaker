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

from spynnaker.pyNN.models.recorder import Recorder as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


class Recorder(_BaseClass):
    """
    .. deprecated:: 6.0
        Use :py:class:`spynnaker.pyNN.models.recorder.Recorder` instead.
    """
    # DO NOT DEFINE SLOTS! Multiple inheritance problems otherwise.
    # __slots__ = []

    def __init__(self, population, vertex):
        """
        :param population: the population to record for
        :type population: ~spynnaker.pyNN.models.populations.Population
        """
        moved_in_v6("spynnaker8.models.recorder",
                    "spynnaker.pyNN.models.recorder")
        super(Recorder, self).__init__(population, vertex)
