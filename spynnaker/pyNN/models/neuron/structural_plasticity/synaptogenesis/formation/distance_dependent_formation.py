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

import numpy
from .abstract_formation import AbstractFormation
from spinn_utilities.overrides import overrides


class DistanceDependentFormation(AbstractFormation):
    """ Formation rule that depends on the physical distance between neurons
    """

    __slots__ = [
        "__grid",
        "__p_form_forward",
        "__sigma_form_forward",
        "__p_form_lateral",
        "__sigma_form_lateral",
        "__ff_distance_probabilities",
        "__lat_distance_probabilities"
    ]

    def __init__(
            self, grid=numpy.array([16, 16]), p_form_forward=0.16,
            sigma_form_forward=2.5, p_form_lateral=1.0,
            sigma_form_lateral=1.0):
        """

        :param grid: (x, y) dimensions of the grid of distance
        :param p_form_forward:\
            The peak probability of formation on feed-forward connections
        :param sigma_form_forward:\
            The spread of probability with distance of formation on\
            feed-forward connections
        :param p_form_lateral:\
            The peak probability of formation on lateral connections
        :param sigma_form_lateral:\
            The spread of probability with distance of formation on\
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
    def vertex_executable_suffix(self):
        return "_distance"

    @overrides(AbstractFormation.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return (4 + 4 + 4 + 4 + len(self.__ff_distance_probabilities) * 2 +
                len(self.__lat_distance_probabilities) * 2)

    def generate_distance_probability_array(self, probability, sigma):
        """ Generate the exponentially decaying probability LUTs.

        :param probability: peak probability
        :type probability: float
        :param sigma: spread
        :type sigma: float
        :return: distance-dependent probabilities
        :rtype: numpy.ndarray(float)
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
        unfiltered_probabilities = quantised_probabilities.astype(
            dtype="uint16")
        # Only return probabilities which are non-zero
        filtered_probabilities = unfiltered_probabilities[
            unfiltered_probabilities > 0]
        if filtered_probabilities.size % 2 != 0:
            filtered_probabilities = numpy.concatenate(
                (filtered_probabilities,
                 numpy.zeros(filtered_probabilities.size % 2, dtype="uint16")))

        return filtered_probabilities

    def distance(self, x0, x1, metric):
        """ Compute the distance between points x0 and x1 place on the grid\
            using periodic boundary conditions.

        :param x0: first point in space
        :type x0: np.ndarray of ints
        :param x1: second point in space
        :type x1: np.ndarray of ints
        :param grid: shape of grid
        :type grid: np.ndarray of ints
        :param metric: distance metric, i.e. euclidian or manhattan
        :type metric: str
        :return: the distance
        :rtype: float
        """
        # pylint: disable=assignment-from-no-return
        x0 = numpy.asarray(x0)
        x1 = numpy.asarray(x1)
        delta = numpy.abs(x0 - x1)
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
    def write_parameters(self, spec):
        spec.write_array(self.__grid)
        spec.write_value(len(self.__ff_distance_probabilities))
        spec.write_value(len(self.__lat_distance_probabilities))
        spec.write_array(self.__ff_distance_probabilities.view("<u4"))
        spec.write_array(self.__lat_distance_probabilities.view("<u4"))

    @overrides(AbstractFormation.get_parameter_names)
    def get_parameter_names(self):
        return ["grid", "p_form_forward", "sigma_form_forward",
                "p_form_lateral", "sigma_form_lateral"]
