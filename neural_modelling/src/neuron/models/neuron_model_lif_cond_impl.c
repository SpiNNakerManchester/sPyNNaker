#include "neuron_model_lif_cond_impl.h"

#include <debug.h>

// for general machine time steps
// defaults to 1ms time step i.e. 10 x 1/10ths of a msec
static uint32_t refractory_time_update = 10;

// simple Leaky I&F ODE - discrete changes elsewhere
/* static inline void _neuron_ode(REAL t, REAL stateVar[], REAL dstateVar_dt[],
                               neuron_pointer_t neuron,
                               input_t input_this_timestep) {

    dstateVar_dt[1] = (( neuron->V_rest - stateVar[1] )
                      + ( neuron->R_membrane * input_this_timestep ))
                      * neuron->one_over_tauRC;
}
*/
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
    static uint8_t refract_threshold_correction[3];
#endif


#ifdef SIMPLE_COMBINED_GRANULARITY
    static uint8_t  simple_thresh_update;
#endif

static inline REAL _correct_for_refractory_granularity(neuron_pointer_t neuron,
        int32_t neg_refract_timer_now) {
    use(neg_refract_timer_now);
    REAL this_eTC = neuron->exp_TC;
#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
    //  within-timestep correction for when neuron came out of refractory period
    // breaks timestep into thirds
    // - average error from approximation = 1/12th of a timestep
    log_debug("ref time %d  ", neg_refract_timer_now);

    if (neg_refract_timer_now < refractory_time_update) {
        // only used if it just came out of refractory period this timestep.
        // So set extra length of time for membrane voltage to develop according
        // to when it came out of ref period
        if (neg_refract_timer_now < neuron->ref_divisions[0]) {

            // came out at end of timestep
            this_eTC = neuron->eTC[0];
        } else if( neg_refract_timer_now > neuron->ref_divisions[1] ) {

            // came out at start of timestep
            this_eTC = neuron->eTC[2];
        } else {

            // otherwise assume in middle third
            this_eTC = neuron->eTC[1];
        }

        log_debug(" ref time %d  eTC  %9.5k \n", neg_refract_timer_now,
                  this_eTC);
    }
#endif // CORRECT_FOR_REFRACTORY_GRANULARITY

#ifdef SIMPLE_COMBINED_GRANULARITY

    // only used if it just came out of refractory period this timestep
    if (neg_refract_timer_now < refractory_time_update) {
        this_eTC = neuron->eTC[1];
    }
#endif // SIMPLE_COMBINED_GRANULARITY
    return this_eTC;
}

// simple Leaky I&F ODE - discrete changes elsewhere -  assumes 1ms timestep?
static inline void _lif_neuron_closed_form(neuron_pointer_t neuron, REAL V_prev,
        int32_t neg_refract_timer_now, input_t input_this_timestep) {

    REAL alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest;

    // this is always the default
    REAL this_eTC = _correct_for_refractory_granularity(neuron,
                                                        neg_refract_timer_now);

    // update membrane voltage
    neuron->V_membrane = alpha - (this_eTC * ( alpha - V_prev ));
}

// ODE solver has just set neuron->V which is current state of membrane voltage
static inline void _neuron_discrete_changes(neuron_pointer_t neuron) {

    // reset membrane voltage
    neuron->V_membrane = neuron->V_reset;

#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY

    // add to refractory timer takes into account already through period
    neuron->refract_timer =
        neuron->T_refract
        - refract_threshold_correction[neuron->prev_spike_code];

    log_debug(" code  %u  thresh ref update %u \n", neuron->prev_spike_code,
              neuron->T_refract
              - refract_threshold_correction[neuron->prev_spike_code] );

#else // CORRECT_FOR_THRESHOLD_GRANULARITY
#ifdef SIMPLE_COMBINED_GRANULARITY

    // one of the simpler ones
    // Expected value of refractory time lost in timestep
    neuron->refract_timer  = neuron->T_refract - simple_thresh_update;
#else // SIMPLE_COMBINED_GRANULARITY

    // reset refractory timer
    neuron->refract_timer  = neuron->T_refract;
#endif // SIMPLE_COMBINED_GRANULARITY
#endif // CORRECT_FOR_THRESHOLD_GRANULARITY
}


// setup function which needs to be called in main program before any neuron
// code executes
// MUST BE: minimum 100, then in 100usec steps...
void neuron_model_set_machine_timestep(timer_t microsecs) {

    const uint16_t time_step_divider = 100;

    // 10 for 1ms time step, 1 for 0.1ms time step which is minimum
    refractory_time_update = microsecs / time_step_divider;

#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
    log_debug("*** Refractory granularity correction");

#endif // CORRECT_FOR_REFRACTORY_GRANULARITY
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
    log_debug("*** Threshold granularity correction");

    refract_threshold_correction[0] =
        (uint8_t) round((double) refractory_time_update * 0.16667);
    refract_threshold_correction[1] =
        (uint8_t) round((double) refractory_time_update * 0.50000);
    refract_threshold_correction[2] =
        (uint8_t) round((double) refractory_time_update * 0.83333);

    log_debug("refractory updates  %u %u %u \n",
              refract_threshold_correction[0],
              refract_threshold_correction[1],
              refract_threshold_correction[2]);
#endif // CORRECT_FOR_THRESHOLD_GRANULARITY
#ifdef SIMPLE_COMBINED_GRANULARITY
    log_debug("*** Simple combined granularity correction");

    // nasty integer divide lets hope it's an even number always!
    simple_thresh_update = refractory_time_update / 2;

    log_debug("refractory_time_update  %u   simp thresh update %u  \n",
              refractory_time_update, simple_thresh_update);
#endif // SIMPLE_COMBINED_GRANULARITY
}


// .277 ms
bool neuron_model_state_update(input_t exc_input, input_t inh_input,
                               input_t external_bias, neuron_pointer_t neuron) {

    bool spike = false;
    REAL V_last = neuron->V_membrane;

    // countdown refractory timer
    neuron->refract_timer -= refractory_time_update;

    // If outside of the refractory period
    if (neuron->refract_timer < 1) {

        // Get the input in nA
        input_t input_this_timestep = exc_input * (neuron->V_rev_E - V_last)
                                      + inh_input * (neuron->V_rev_I - V_last)
                                      + external_bias + neuron->I_offset;

        _lif_neuron_closed_form(neuron, V_last, -neuron->refract_timer,
                                input_this_timestep);

        // has it spiked?
        spike = REAL_COMPARE(neuron->V_membrane, >=, neuron->V_thresh);

#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
        if (spike) {

            REAL A, B, thresh;

            // calculate the two simple linear indicators of where the
            // threshold was cut
            thresh = neuron->V_thresh;

            A = neuron->V_membrane - thresh;
            B = thresh - V_last;

            if ( A >= 2*B ) {

                // it spiked in first third
                neuron->prev_spike_code = 2;
            } else if  ( B >= 2*A ) {

                // it spiked in last third
                neuron->prev_spike_code = 0;
            } else {

                // it spiked near middle
                neuron->prev_spike_code = 1;
            }

            log_debug(" A %9.4k   B %9.4k  code %u \n", A, B,
                      neuron->prev_spike_code);

            _neuron_discrete_changes( neuron );
        }

#else // CORRECT_FOR_THRESHOLD_GRANULARITY
        // works for both no correction and simple correction case
        if (spike) {
            _neuron_discrete_changes( neuron );
        }
#endif // CORRECT_FOR_THRESHOLD_GRANULARITY
    }

    return spike;
}

state_t neuron_model_get_membrane_voltage(neuron_pointer_t neuron) {
    return neuron->V_membrane;
}


// printout of neuron definition and state variables
void neuron_model_print(restrict neuron_pointer_t neuron) {
    log_debug("V membrane    = %11.4k mv", neuron->V_membrane);
    log_debug("V thresh      = %11.4k mv", neuron->V_thresh);
    log_debug("V reset       = %11.4k mv", neuron->V_reset);
    log_debug("V rest        = %11.4k mv", neuron->V_rest);

    log_info( "V reversal E  = %11.4k mv", neuron->V_rev_E );
    log_info( "V reversal I  = %11.4k mv", neuron->V_rev_I );

    log_debug("I offset      = %11.4k nA", neuron->I_offset);
    log_debug("R membrane    = %11.4k Mohm", neuron->R_membrane);

    log_debug("exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC);

    log_debug("T refract     = %u microsecs", neuron->T_refract * 100);
}

// this is used to set up the eTC array if any TQ is being corrected for,
// not currently used in production code
//#define   TEST_0p1
#define TQ_TEST_CODE \
    #ifdef TEST_0p1 \
        double scale = 0.1; \
    #else \
        double scale = 1.0; \
    #endif   \
    neuron->eTC[0] = (REAL) exp(-(double)one_over_tauRC * 1.16666667 * scale); \
    neuron->eTC[1] = (REAL) exp(-(double)one_over_tauRC * 1.5 * scale); \
    neuron->eTC[2] = (REAL) exp(-(double)one_over_tauRC * 1.83333333 * scale); \
    neuron->exp_TC = (REAL) exp(-(double)one_over_tauRC * scale); \
    log_debug("eTC  %9.5k %9.5k %9.5k \n", neuron->eTC[0], neuron->eTC[1], \
              neuron->eTC[2]);

//
neuron_pointer_t neuron_model_lif_cond_impl_create(REAL V_thresh, REAL V_reset,
        REAL V_rest, REAL V_rev_E, REAL V_rev_I, REAL one_over_tauRC, REAL R,
        int32_t T_refract, REAL V, REAL I, int32_t refract_timer, REAL exp_tc) {
    neuron_pointer_t neuron = spin1_malloc(sizeof(neuron_t));

    neuron->V_membrane = V;
    neuron->V_thresh = V_thresh;
    neuron->V_reset = V_reset;
    neuron->V_rest = V_rest;

    neuron->V_rev_E = V_rev_E;
    neuron->V_rev_I = V_rev_I;

    neuron->I_offset = I;
    neuron->R_membrane = R;
    neuron->one_over_tauRC = one_over_tauRC;
    neuron->exp_TC = exp_tc;

    neuron->T_refract = T_refract;
    neuron->refract_timer = refract_timer;

#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY

    // only works properly for 1000, 700, 400 microsec timesteps
    neuron->ref_divisions[0] =
        (uint8_t) round((refractory_time_update-1) /* ms/10 */* 0.33333);
    neuron->ref_divisions[1] =
        (uint8_t) round((refractory_time_update-1) /* ms/10 */* 0.66667);

    log_debug("NRF  %d  %d \n", neuron->ref_divisions[0],
              neuron->ref_divisions[1]);
#endif

// these set up the eTC[] array if it is required for TQ corrections
#ifdef SIMPLE_COMBINED_GRANULARITY
    TQ_TEST_CODE
#endif
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
    TQ_TEST_CODE
#endif
#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
#ifndef CORRECT_FOR_THRESHOLD_GRANULARITY
    TQ_TEST_CODE
#endif
#endif

    return neuron;
}
