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

from spinn_utilities.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractPopulationSettable


class SimplePopulationSettable(
        AbstractPopulationSettable, allow_derivation=True):
    """ An object all of whose properties can be accessed from a PyNN\
        Population i.e. no properties are hidden
    """

    __slots__ = ()

    @overrides(AbstractPopulationSettable.get_value)
    def get_value(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise Exception("Population {} does not have parameter {}".format(
            self, key))

    @overrides(AbstractPopulationSettable.set_value)
    def set_value(self, key, value):
        if not hasattr(self, key):
            raise Exception("Parameter {} not found".format(key))
        setattr(self, key, value)
