import numpy

from spynnaker.pyNN import exceptions


def write_exp_synapse_param(tau, machine_time_step, vertex_slice, spec):

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

        # Copy for all atoms
        # **YUCK** this is inefficient in terms of DSG
        for _ in range(vertex_slice.n_atoms):
            spec.write_value(data=rescaled_decay[0])
            spec.write_value(data=rescaled_init[0])

    # Otherwise, if we have generated decays and inits for each atom
    elif (rescaled_decay.size > vertex_slice.hi_atom
            and rescaled_init.size > vertex_slice.hi_atom):

        # Interleave into one array
        interleaved_params = numpy.empty(vertex_slice.n_atoms * 2)
        interleaved_params[0::2] = \
            rescaled_decay[vertex_slice.lo_atom:vertex_slice.hi_atom + 1]
        interleaved_params[1::2] = \
            rescaled_init[vertex_slice.lo_atom:vertex_slice.hi_atom + 1]

        spec.write_array(interleaved_params)
    else:
        raise exceptions.SynapticBlockGenerationException(
            "Cannot generate synapse parameters from %u values"
            % rescaled_decay.size)
