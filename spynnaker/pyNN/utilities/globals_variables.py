from spynnaker.pyNN.utilities.failed_state import FailedState

# only map the simulator to the FailedState, if it has not already been set
try:
    simulator
except NameError:
    simulator = FailedState()


def get_simulator():
    global simulator
    return simulator


def set_simulator(new_simulator):
    global simulator
    simulator = new_simulator
