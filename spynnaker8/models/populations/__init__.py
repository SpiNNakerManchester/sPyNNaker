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

"""
Populations are objects that contain groups of neurons.

.. deprecated:: 6.0
    Use :py:mod:`spynnaker.pyNN.models.populations` instead.
"""

from .assembly import Assembly
from .population import Population
from .population_view import PopulationView

__all__ = ["Assembly", "Population", "PopulationView"]
