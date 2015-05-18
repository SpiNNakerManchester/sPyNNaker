#include "neuron_model_izh_curr_impl.h"
#include "../../common/constants.h"

#include <debug.h>

// machine timestep in msecs
static REAL machine_timestep = REAL_CONST(1.0);

static const REAL V_threshold = REAL_CONST(30.0);

/*! \brief For linear membrane voltages, 1.5 is the correct value. However
 * with actual membrane voltage behaviour and tested over an wide range of
 * use cases 1.85 gives slightly better spike timings.
 */
static const REAL SIMPLE_TQ_OFFSET = REAL_CONST(1.85);

/////////////////////////////////////////////////////////////
// definition for Izhikevich neuron
/*static inline void _neuron_ode(
        REAL t, REAL stateVar[], REAL dstateVar_dt[],
        neuron_pointer_t neuron, REAL input_this_timestep) {

    REAL V_now = stateVar[1];
    REAL U_now = stateVar[2];
    log_debug(" sv1 %9.4k  V %9.4k --- sv2 %9.4k  U %9.4k\n", stateVar[1],
              neuron->V, stateVar[2], neuron->U);

    // Update V
    dstateVar_dt[1] =
        REAL_CONST(140.0)
        + (REAL_CONST(5.0) + REAL_CONST(0.0400) * V_now) * V_now - U_now
        + input_this_timestep;

    // Update U
    dstateVar_dt[2] = neuron->A * (neuron->B * V_now - U_now);
} */

/*!
 * \brief Midpoint is best balance between speed and accuracy so far from
 * ODE solve comparison work paper shows that Trapezoid version gives better
 * accuracy at small speed cost
 * \param[in] h
 * \param[in] neuron
 * \param[in] input_this_timestep
 */
static inline void _rk2_kernel_midpoint(REAL h, neuron_pointer_t neuron,
                                        REAL input_this_timestep) {

    // to match Mathematica names
    REAL lastV1 = neuron->V;
    REAL lastU1 = neuron->U;
    REAL a = neuron->A;
    REAL b = neuron->B;

    REAL pre_alph = REAL_CONST(140.0) + input_this_timestep - lastU1;
    REAL alpha = pre_alph
                 + ( REAL_CONST(5.0) + REAL_CONST(0.0400) * lastV1) * lastV1;
    REAL eta = lastV1 + REAL_HALF(h * alpha);

    // could be represented as a long fract?
    REAL beta = REAL_HALF(h * (b * lastV1 - lastU1) * a);

    neuron->V += h * (pre_alph - beta
                      + ( REAL_CONST(5.0) + REAL_CONST(0.0400) * eta) * eta);

    neuron->U += a * h * (-lastU1 - beta + b * eta);
}

// ODE solver has just set neuron->V which is current state of membrane voltage
static inline void _neuron_discrete_changes(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V = neuron->C;

    // offset 2nd state variable
    neuron->U += neuron->D;
}

void neuron_model_set_machine_timestep(timer_t microsecs) {

    const double time_step_multiplier = 0.00100;
    machine_timestep = (REAL) (microsecs * time_step_multiplier);
}

//
bool neuron_model_state_update(input_t exc_input, input_t inh_input,
                               input_t external_bias, neuron_pointer_t neuron) {

    // Get the input in nA
	/* TODO
	 * this is where the abstracted create_input_current() function will be used
	 *      static inline REAL create_input_current( REAL exc_input,
	 *                                               REAL inh_input,
	 *                                               REAL i_offset );
	 *   to generalise current and conductance input i.e.
	 *   input_this_timestep = create_input_current( exc_input, inh_input,
	 *                                               neuron->I_offset );
	 */
    input_t input_this_timestep = exc_input - inh_input
                                  + external_bias + neuron->I_offset;

    // the best AR update so far
    _rk2_kernel_midpoint(neuron->this_h, neuron, input_this_timestep);

    /* TODO
     * this is where the abstracted test_threshold() function will be used
     *     static inline bool test_threshold( accum membrane, accum threshold );
     * to allow stochastic neurons if necessary i.e.
     * bool spike = test_threshold( neuron->V, V_threshold );
     */

    bool spike = REAL_COMPARE(neuron->V, >=, V_threshold);

    if (spike) {
        _neuron_discrete_changes(neuron);

        // simple threshold correction - next timestep (only) gets a bump
        neuron->this_h = machine_timestep * SIMPLE_TQ_OFFSET;
    } else {
        neuron->this_h = machine_timestep;
    }

    return spike;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V;
}

// printout of neuron definition and state variables
void neuron_model_print(restrict neuron_pointer_t neuron) {
    log_debug("A = %11.4k ", neuron->A);
    log_debug("B = %11.4k ", neuron->B);
    log_debug("C = %11.4k ", neuron->C);
    log_debug("D = %11.4k ", neuron->D);

    log_debug("V = %11.4k ", neuron->V);
    log_debug("U = %11.4k ", neuron->U);

    log_debug("I = %11.4k \n", neuron->I_offset);
}

//
neuron_pointer_t neuron_model_izh_curr_impl_create(REAL A, REAL B, REAL C,
                                                   REAL D, REAL V, REAL U,
                                                   REAL I) {
    neuron_pointer_t neuron = spin1_malloc(sizeof(neuron_t));

    neuron->A = A;
    neuron->B = B;
    neuron->C = C;
    neuron->D = D;

    neuron->V = V;
    neuron->U = U;

    neuron->I_offset = I;

    neuron->this_h = machine_timestep * REAL_CONST(1.001);
    neuron_model_print(neuron);
    log_debug("h = %11.4k ms\n", neuron->this_h);

    return neuron;
}
