import numpy
from .abstract_formation import AbstractFormation
from pacman.model.decorators.overrides import overrides
from data_specification.enums import DataType


class DistanceDependentFormation(AbstractFormation):
    """ Formation rule that depends on the physical distance between neurons
    """

    __slots__ = [
        "_grid",
        "_p_form_forward",
        "_sigma_form_forward",
        "_p_form_lateral",
        "_sigma_form_lateral",
        "__ff_distance_probabilities",
        "__lat_distance_probabilities"
    ]

    def __init__(
            self, grid, p_form_forward, sigma_form_forward, p_form_lateral,
            sigma_form_lateral):
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
        self._grid = numpy.asarray(grid, dtype=int)
        self._p_form_forward = p_form_forward
        self._sigma_form_forward = sigma_form_forward
        self._p_form_lateral = p_form_lateral
        self._sigma_form_lateral = sigma_form_lateral

        self.__ff_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_forward, self.__sigma_form_forward)
        self.__lat_distance_probabilities = \
            self.generate_distance_probability_array(
                self.__p_form_lateral, self.__sigma_form_lateral)

    @overrides(AbstractFormation.is_same_as)
    def is_same_as(self, other):
        if not isinstance(other, DistanceDependentFormation):
            return False
        return (self._grid == other._grid and
                self._p_form_forward == other._p_form_forward and
                self._sigma_form_forward == other._sigma_form_forward and
                self._p_form_lateral == other._p_form_lateral and
                self._sigma_form_lateral == other.sigma_form_lateral)

    @property
    @overrides(AbstractFormation.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_distance"

    @overrides(AbstractFormation.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return (4 + 4 + 4 + 4 + len(self.__ff_distance_probabilities) * 2 +
                len(self.__lat_distance_probabilities) * 2)

    @overrides(AbstractFormation.write_parameters)
    def write_parameters(self, spec):
        spec.write_array(self._grid)
        spec.write_value(len(self.__ff_distance_probabilities))
        spec.write_value(len(self.__lat_distance_probabilities))
        spec.write_array(self.__ff_distance_probabilities.view(dtype="<u2"),
                         data_type=DataType.UINT16)
        spec.write_array(self.__lat_distance_probabilities.view(dtype="<u2"),
                         data_type=DataType.UINT16)

    @overrides(AbstractFormation.get_parameter_names)
    def get_parameter_names(self):
        return ["grid", "p_form_forward", "sigma_form_forward",
                "p_form_lateral", "sigma_form_lateral"]
