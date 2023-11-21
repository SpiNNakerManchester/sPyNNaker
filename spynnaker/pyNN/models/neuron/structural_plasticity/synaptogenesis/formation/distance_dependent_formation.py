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

import numpy
from numpy import uint16, floating
from numpy.typing import ArrayLike, NDArray
from typing import Iterable
from spinn_utilities.overrides import overrides
from spinn_front_end_common.interface.ds import (
    DataType, DataSpecificationBase)
from spinn_front_end_common.utilities.constants import (
    BYTES_PER_WORD, BYTES_PER_SHORT)
from .abstract_formation import AbstractFormation

# 6 32-bit words (grid_x, grid_y, grid_x_recip, grid_y_recep, ff_prob_size,
#                 lat_prob_size)
_PARAMS_SIZE_IN_BYTES = 6 * BYTES_PER_WORD


class DistanceDependentFormation(AbstractFormation):
    """
    Formation rule that depends on the physical distance between neurons.
    """

    __slots__ = (
        "__grid",
        "__p_form_forward",
        "__sigma_form_forward",
        "__p_form_lateral",
        "__sigma_form_lateral",
        "__ff_distance_probabilities",
        "__lat_distance_probabilities")

    def __init__(
            self, grid: ArrayLike = (16, 16), p_form_forward: float = 0.16,
            sigma_form_forward: float = 2.5, p_form_lateral: float = 1.0,
            sigma_form_lateral: float = 1.0):
        """
        :param grid: (x, y) dimensions of the grid of distance
        :type grid: tuple(int,int) or list(int) or ~numpy.ndarray(int)
        :param float p_form_forward:
            The peak probability of formation on feed-forward connections
        :param float sigma_form_forward:
            The spread of probability with distance of formation on
            feed-forward connections
        :param float p_form_lateral:
            The peak probability of formation on lateral connections
        :param float sigma_form_lateral:
            The spread of probability with distance of formation on
            lateral connections
        """
        self.__grid = numpy.asarray(grid, dtype=int)
        self.__p_form_forward = p_form_forward
        self.__sigma_form_forward = sigma_form_forward
        self.__p_form_lateral = p_form_lateral
        self.__sigma_form_lateral = sigma_form_lateral

        self.__ff_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_forward, self.__sigma_form_forward)
        self.__lat_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_lateral, self.__sigma_form_lateral)

    @property
    @overrides(AbstractFormation.vertex_executable_suffix)
    def vertex_executable_suffix(self) -> str:
        return "_distance"

    @overrides(AbstractFormation.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self) -> int:
        return (_PARAMS_SIZE_IN_BYTES +
                len(self.__ff_distance_probabilities) * BYTES_PER_SHORT +
                len(self.__lat_distance_probabilities) * BYTES_PER_SHORT)

    def generate_distance_probability_array(
            self, probability: float, sigma: float) -> NDArray[uint16]:
        """
        Generate the exponentially decaying probability LUTs.

        :param float probability: peak probability
        :param float sigma: spread
        :return: distance-dependent probabilities
        :rtype: ~numpy.ndarray(float)
        """
        euclidian_distances = numpy.ones(self.__grid ** 2) * numpy.nan
        for row in range(euclidian_distances.shape[0]):
            for column in range(euclidian_distances.shape[1]):
                if self.__grid[0] > 1:
                    pre = (row // self.__grid[0], row % self.__grid[1])
                    post = (column // self.__grid[0], column % self.__grid[1])
                else:
                    pre = (0, row % self.__grid[1])
                    post = (0, column % self.__grid[1])

                # TODO Make distance metric "type" controllable
                euclidian_distances[row, column] = self.distance(
                    pre, post, metric='euclidian')
        largest_squared_distance = numpy.max(euclidian_distances ** 2)
        squared_distances = numpy.arange(largest_squared_distance + 1)
        raw_probabilities = probability * (
            numpy.exp(-squared_distances / (2 * sigma ** 2)))
        quantised_probabilities = raw_probabilities * ((2 ** 16) - 1)
        # Quantize probabilities and cast as uint16 / short
        unfiltered_probabilities = quantised_probabilities.astype(uint16)
        # Only return probabilities which are non-zero
        filtered_probabilities = unfiltered_probabilities[
            unfiltered_probabilities > 0]
        if filtered_probabilities.size % BYTES_PER_SHORT != 0:
            filtered_probabilities = numpy.concatenate(
                (filtered_probabilities,
                 numpy.zeros(filtered_probabilities.size % BYTES_PER_SHORT,
                             dtype=uint16)))

        return filtered_probabilities

    def distance(
            self, x0: ArrayLike, x1: ArrayLike, metric) -> NDArray[floating]:
        """
        Compute the distance between points x0 and x1 place on the grid
        using periodic boundary conditions.

        :param ~numpy.ndarray(int) x0: first point in space
        :param ~numpy.ndarray(int) x1: second point in space
        :param ~numpy.ndarray(int) grid: shape of grid
        :param str metric:
            distance metric, i.e. ``euclidian`` or ``manhattan`` or
            ``equidistant``
        :return: the distance
        :rtype: float
        """
        delta = numpy.abs(numpy.asarray(x0) - numpy.asarray(x1))
        if (delta[0] > self.__grid[0] * .5) and self.__grid[0] > 0:
            delta[0] -= self.__grid[0]

        if (delta[1] > self.__grid[1] * .5) and self.__grid[1] > 0:
            delta[1] -= self.__grid[1]

        if metric == 'manhattan':
            return numpy.abs(delta).sum(axis=-1)
        elif metric == 'equidistant':
            p = 4
            exponents = numpy.power(delta, [p] * delta.size)
            return numpy.floor(numpy.power(exponents.sum(axis=-1), [1. / p]))
        return numpy.sqrt((delta ** 2).sum(axis=-1))

    @overrides(AbstractFormation.write_parameters)
    def write_parameters(self, spec: DataSpecificationBase):
        spec.write_array(self.__grid)
        # Work out the reciprocal, but zero them if >= 1 as they are not
        # representable as S031 in that case, and not used anyway
        recip = 1 / self.__grid
        recip[recip >= 1.0] = 0
        spec.write_array(DataType.S031.encode_as_numpy_int_array(recip))
        spec.write_value(len(self.__ff_distance_probabilities))
        spec.write_value(len(self.__lat_distance_probabilities))
        spec.write_array(self.__ff_distance_probabilities.view("<u4"))
        spec.write_array(self.__lat_distance_probabilities.view("<u4"))

    @overrides(AbstractFormation.get_parameter_names)
    def get_parameter_names(self) -> Iterable[str]:
        return ("grid", "p_form_forward", "sigma_form_forward",
                "p_form_lateral", "sigma_form_lateral")
