# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
