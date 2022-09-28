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

from spynnaker.pyNN.models.populations import Population as _BaseClass
from spynnaker.pyNN.utilities.utility_calls import moved_in_v6


# pylint: disable=abstract-method
class Population(_BaseClass):
    """ PyNN 0.9 population object.

    .. deprecated:: 6.0
        Use
        :py:class:`spynnaker.pyNN.models.populations.Population` instead.
    """

    def __init__(
            self, size, cellclass, cellparams=None, structure=None,
            initial_values=None, label=None, additional_parameters=None):
        """
        :param int size: The number of neurons in the population
        :param cellclass: The implementation of the individual neurons.
        :type cellclass: type or AbstractPyNNModel
        :param cellparams: Parameters to pass to ``cellclass`` if it
            is a class to instantiate. Must be ``None`` if ``cellclass`` is an
            instantiated object.
        :type cellparams: dict(str,object) or None
        :param ~pyNN.space.BaseStructure structure:
        :param dict(str,float) initial_values:
            Initial values of state variables
        :param str label: A label for the population
        :param additional_parameters:
            Additional parameters to pass to the vertex creation function.
        :type additional_parameters: dict(str, ...)
        """
        # pylint: disable=too-many-arguments
        moved_in_v6("spynnaker8.models.populations.Population",
                    "spynnaker.pyNN.models.populations.Population")
        super(Population, self).__init__(
            size, cellclass, cellparams, structure, initial_values, label,
            additional_parameters)
