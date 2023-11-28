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

import pyNN.random
from pyNN.random import NumpyRNG
from typing import Optional
from pyNN.random import available_distributions
# This file is to work around a Sphinx bug

if "exponential_clipped" not in available_distributions:
    available_distributions["exponential_clipped"] = ('beta', 'low', 'high')


class RandomDistribution(pyNN.random.RandomDistribution):
    """
    Class which defines a next(n) method which returns an array of ``n``
    random numbers from a given distribution.

    Examples::

        >>> rd = RandomDistribution('uniform', (-70, -50))
        >>> rd = RandomDistribution('normal', mu=0.5, sigma=0.1)
        >>> rng = NumpyRNG(seed=8658764)
        >>> rd = RandomDistribution('gamma', k=2.0, theta=5.0, rng=rng)

    .. list-table:: Available distributions
        :widths: auto
        :header-rows: 1

        * - Name
          - Parameters
          - Comments
        * - ``binomial``
          - ``n``, ``p``
          -
        * - ``gamma``
          - ``k``, ``theta``
          -
        * - ``exponential``
          - ``beta``
          -
        * - ``lognormal``
          - ``mu``, ``sigma``
          -
        * - ``normal``
          - ``mu``, ``sigma``
          -
        * - ``normal_clipped``
          - ``mu``, ``sigma``, ``low``, ``high``
          - Values outside (``low``, ``high``) are redrawn
        * - ``normal_clipped_to_boundary``
          - ``mu``, ``sigma``, ``low``, ``high``
          - Values below/above ``low``/``high`` are set to ``low``/``high``
        * - ``poisson``
          - ``lambda_``
          - Trailing underscore since ``lambda`` is a Python keyword
        * - ``uniform``
          - ``low``, ``high``
          -
        * - ``uniform_int``
          - ``low``, ``high``
          - Only generates integer values
        * - ``vonmises``
          - ``mu``, ``kappa``
          -
    """
    # TODO: should uniform_int be randint to match utility_calls.STATS_BY_NAME?

    # Pylint is wrong about the super-delegation being useless
    def __init__(  # pylint: disable=useless-super-delegation
            self, distribution: str, parameters_pos: Optional[tuple] = None,
            rng: Optional[NumpyRNG] = None, **parameters_named):
        """
        :param str distribution: the name of a random number distribution.
        :param parameters_pos:
            parameters of the distribution, provided as a tuple. For the
            correct ordering, see `random.available_distributions`.
        :type parameters_pos: tuple or None
        :param rng: the random number generator to use, if a specific one is
            desired (e.g., to provide a seed).
        :type rng: ~pyNN.random.NumpyRNG or ~pyNN.random.GSLRNG or
            ~pyNN.random.NativeRNG or None
        :param parameters_named:
            parameters of the distribution, provided as keyword arguments.

        Parameters may be provided either through ``parameters_pos`` or through
        ``parameters_named``, but not both. All parameters must be provided,
        there are no default values. Parameter names are, in general, as used
        in Wikipedia.
        """
        super().__init__(distribution, parameters_pos, rng, **parameters_named)

    def __repr__(self):
        return self.__str__()
