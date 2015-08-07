import numpy

from spynnaker.pyNN import exceptions


def write_exp_synapse_param(tau, machine_time_step, spec):

    # Calculate decay and initialisation values
    decay = numpy.exp(numpy.divide(-float(machine_time_step),
                                   numpy.multiply(1000.0, tau)))
    init = numpy.multiply(numpy.multiply(tau, numpy.subtract(1.0, decay)),
                          (1000.0 / float(machine_time_step)))

    # Scale to fixed-point
    scale = float(pow(2, 32))
    rescaled_decay = numpy.multiply(decay, scale).astype("uint32")
    rescaled_init = numpy.multiply(init, scale).astype("uint32")

    # If we only generated a single param
    if rescaled_decay.size == 1 and rescaled_init.size == 1:
        spec.write_value(data=rescaled_decay[0])
        spec.write_value(data=rescaled_init[0])

    # Otherwise, give an error
    else:
        raise exceptions.SynapticBlockGenerationException(
            "Cannot generate synapse parameters from %u values"
            % rescaled_decay.size)
