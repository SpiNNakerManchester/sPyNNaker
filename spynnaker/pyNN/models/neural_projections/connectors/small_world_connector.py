from spynnaker.pyNN.models.neural_projections.connectors.abstract_connector \
    import AbstractConnector


class SmallWorldConnector(AbstractConnector):

    def __init__(
            self, degree, rewiring, allow_self_connections=True, weights=0.0,
            delays=1, space=None, safe=True, verbose=False,
            n_connections=None):
        AbstractConnector.__init__(self, safe, space, verbose)
        self._rewiring = rewiring

        self._check_parameters(weights, delays, allow_lists=False)
        if n_connections is not None:
            raise NotImplementedError(
                "n_connections is not implemented for"
                " SmallWorldConnector on this platform")

        # Get the probabilities up-front for now
        # TODO: Work out how this can be done statistically
        pre_positions = self._pre_population.positions
        post_positions = self._post_population.positions
        distances = self._space.distances(
            pre_positions, post_positions, False)
        self._probs = (distances < degree).as_type("u4")
