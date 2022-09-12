# Copyright (c) 2017-2022 The University of Manchester
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

from pyNN import common as pynn_common


class Assembly(pynn_common.Assembly):
    """
    A group of neurons, may be heterogeneous, in contrast to a Population
    where all the neurons are of the same type.

    :param populations: the populations or views to form the assembly out of
    :type populations: ~spynnaker.pyNN.models.populations.Population or
        ~spynnaker.pyNN.models.populations.PopulationView
    :param kwargs: may contain `label` (a string describing the assembly)
    """
