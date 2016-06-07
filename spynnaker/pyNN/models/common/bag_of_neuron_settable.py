

class BagOfNeuronSettable(object):
    """
    helper method for holding basic set and gets for stuff that uses
    bag of neurons
    """

    def __init__(self):
        pass

    @staticmethod
    def _set_param(param, value, atoms):
        for atom in atoms:
            atom.set(param, value)

    @staticmethod
    def _get_param(param, atoms):
        data = list()
        for atom in atoms:
            data.append(atom.get(param))
        return data

    @staticmethod
    def _set_state_variable(param, value, atoms):
        for atom, value in zip(atoms, value):
            atom.set_param(param, value)

    @staticmethod
    def _get_state_variable(param, atoms):
        data = list()
        for atom in atoms:
            data.append(atom.get_state_variable(param))
        return data
