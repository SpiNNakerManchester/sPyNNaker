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
from spynnaker.pyNN.models.populations import Assembly as _BaseClass
logger = FormatAdapter(logging.getLogger(__name__))


class Assembly(_BaseClass):
    """
    A group of neurons, may be heterogeneous, in contrast to a Population
    where all the neurons are of the same type.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.populations.Assembly` instead.
    """

    def __init__(self, *populations, **kwargs):
        """
        :param populations:
            the populations or views to form the assembly out of
        :type populations: ~spynnaker.pyNN.models.populations.Population or
            ~spynnaker.pyNN.models.populations.PopulationView
        :param kwargs: may contain `label` (a string describing the assembly)
        """
        super(Assembly, self).__init__(*populations, **kwargs)
        logger.warning(
            "please use spynnaker.pyNN.models.populations.Assembly instead")
