from pacman.model.abstract_classes.abstract_constrained_vertex import \
    AbstractConstrainedVertex


class PartitionedVertex(AbstractConstrainedVertex):
    """ Represents a sub-set of atoms from a AbstractConstrainedVertex
    """

    def __init__(self, resources_required, label, constraints=None):
        """
        :param resources_required: The approximate resources needed for\
                                   the vertex
        :type resources_required:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :param label: The name of the subvertex
        :type label: str
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
        """
        AbstractConstrainedVertex.__init__(self, label=label,
                                           constraints=constraints)
        self._resources_required = resources_required

    @property
    def resources_required(self):
        """The resources that vertex requires

        :return: The resources required by the vertex
        :rtype:\
                    :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :raise None: Raises no known exceptions
        """
        return self._resources_required

    def __str__(self):
        return self._label
