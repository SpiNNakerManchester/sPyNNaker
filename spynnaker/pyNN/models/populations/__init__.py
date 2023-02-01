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
A population is a group of neurons with the same neuron model and synaptic
model, but possibly (usually!) varying connectivity and configuration
parameters.

A population view is a subset of a population, created by slicing the
population::

    view = population[n:m]

An assembly is an agglomeration of populations and population views, created
by adding them together::

    assembly = population_1 + population_2

.. note::
    sPyNNaker only has incomplete support for assemblies; do not use.
"""

from .assembly import Assembly
from .population_base import PopulationBase
from .population import Population
from .population_view import PopulationView, IDMixin

__all__ = ["Assembly", "IDMixin", "Population", "PopulationBase",
           "PopulationView"]
