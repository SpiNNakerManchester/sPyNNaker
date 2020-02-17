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

from .abstract_accepts_incoming_synapses import AbstractAcceptsIncomingSynapses
from .abstract_contains_units import AbstractContainsUnits
from .abstract_filterable_edge import AbstractFilterableEdge
from .abstract_population_initializable import AbstractPopulationInitializable
from .abstract_population_settable import AbstractPopulationSettable
from .abstract_read_parameters_before_set import (
    AbstractReadParametersBeforeSet)
from .abstract_settable import AbstractSettable
from .abstract_weight_updatable import AbstractWeightUpdatable

__all__ = ["AbstractAcceptsIncomingSynapses", "AbstractContainsUnits",
           "AbstractFilterableEdge", "AbstractPopulationInitializable",
           "AbstractPopulationSettable", "AbstractReadParametersBeforeSet",
           "AbstractSettable", "AbstractWeightUpdatable"]
