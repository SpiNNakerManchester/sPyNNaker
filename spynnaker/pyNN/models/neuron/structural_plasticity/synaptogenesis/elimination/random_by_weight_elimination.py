from .abstract_elimination import AbstractElimination
from pacman.model.decorators.overrides import overrides


class RandomByWeightElimination(AbstractElimination):
    """ Elimination Rule that depends on the weight of a synapse
    """

    __slots__ = [
        "_prob_elim_depression",
        "_prob_elim_potentiation",
        "_mid_weight"
    ]

    def __init__(
            self, prob_elim_depression, prob_elim_potentiation, mid_weight):
        """

        :param prob_elim_depression:\
            The probability of elimination if the weight has been depressed\
            (ignored on static weight connections)
        :param prob_elim_potentiation:\
            The probability of elimination of the weight has been potentiated\
            or has not changed (and also used on static weight connections)
        :param mid_weight:\
            Below this weight is considered depression, above or equal to this\
            weight is considered potentiation (or the static weight of the\
            connection on static weight connections)
        """
        self._prob_elim_depression = prob_elim_depression
        self._prob_elim_potentiation = prob_elim_potentiation
        self._mid_weight = mid_weight

    @property
    @overrides(AbstractElimination.vertex_executable_suffix)
    def vertex_executable_suffix(self):
        return "_weight"

    @overrides(AbstractElimination.get_parameters_sdram_usage_in_bytes)
    def get_parameters_sdram_usage_in_bytes(self):
        return 3 * 4

    @overrides(AbstractElimination.write_parameters)
    def write_parameters(self, spec):
        spec.write_value(self._prob_elim_depression)
        spec.write_value(self._prob_elim_potentiation)
        spec.write_value(self._mid_weight)

    @overrides(AbstractElimination.get_parameter_names)
    def get_parameter_names(self):
        return ["prob_elim_depression", "prob_elim_potentiation", "mid_weight"]
