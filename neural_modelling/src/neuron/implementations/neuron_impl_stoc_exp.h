#ifndef _MY_FULL_NEURON_IMPL_
#define _MY_FULL_NEURON_IMPL_

// Demonstrating that a "neuron model" can be defined in a different
// way without the use of components for additional input / input / threshold

#include <neuron/implementations/neuron_impl.h>
#include <spin1_api.h>
#include <debug.h>
#include <random.h>
#include <stdfix-full-iso.h>
#include <common/maths-util.h>

#define V_RECORDING_INDEX 0
#define EX_INPUT_INDEX 1
#define IN_INPUT_INDEX 2
#define N_RECORDED_VARS 3

#define SPIKE_RECORDING_BITFIELD 0
#define N_BITFIELD_VARS 1

#include <neuron/neuron_recording.h>

#include <neuron/current_sources/current_source_impl.h>
#include <neuron/current_sources/current_source.h>

//! definition of neuron parameters
typedef struct neuron_params_t {

    //! The tau value of the neuron
    UREAL tau_ms;

    //! The timestep of the neuron being used
    UREAL time_step;

    //! The bias value
    REAL bias;

    //! The initial refractory timer
    uint32_t refract_init;

    //! Random seed to use
    mars_kiss64_seed_t random_seed;
} neuron_params_t;


//! definition of neuron state
typedef struct neuron_impl_t {

    //! The reciprocal of the tau value
    UREAL tau_recip;

    //! The maximum left shift that will overflow on tau_recip
    uint32_t max_left_shift;

    //! The maximum right shift that will underflow on tau_recip
    uint32_t max_right_shift;

    //! The bias value
    REAL bias;

    //! The refractory timer countdown value
    uint32_t t_refract;

    //! The refractory timer
    uint32_t refract_timer;

    //! The random state
    mars_kiss64_seed_t random_seed;

    //! The inputs to add in the next timestep
    input_t inputs[2];
} neuron_impl_t;

//! Array of neuron states
static neuron_impl_t *neuron_array;

SOMETIMES_UNUSED // Marked unused as only used sometimes
static bool neuron_impl_initialise(uint32_t n_neurons) {
    // Allocate DTCM for neuron array
    if (sizeof(neuron_impl_t) != 0) {
        neuron_array = spin1_malloc(n_neurons * sizeof(neuron_impl_t));
        if (neuron_array == NULL) {
            log_error("Unable to allocate neuron array - Out of DTCM");
            return false;
        }
    }

    return true;
}

static inline uint32_t stoc_exp_ceil_accum(UREAL value) {
	uint32_t bits = bitsuk(value);
	uint32_t integer = bits >> 16;
	uint32_t fraction = bits & 0xFFFF;
	if (fraction > 0) {
	    return integer + 1;
	}
	return integer;
}

static inline void neuron_model_initialise(
		neuron_impl_t *state, neuron_params_t *params) {
	UREAL ts = params->time_step;
	state->tau_recip = ukdivuk(UREAL_CONST(1.0), params->tau_ms);
	state->max_left_shift = __builtin_clz(bitsuk(state->tau_recip));
	state->max_right_shift = __builtin_ctz(bitsuk(state->tau_recip));
	state->bias = params->bias;
	state->t_refract = stoc_exp_ceil_accum(ukdivuk(params->tau_ms, ts));
    state->refract_timer = params->refract_init;
    spin1_memcpy(state->random_seed, params->random_seed, sizeof(mars_kiss64_seed_t));
    validate_mars_kiss64_seed(state->random_seed);
}

static inline void neuron_model_save_state(neuron_impl_t *state, neuron_params_t *params) {
	params->refract_init = state->refract_timer;
	spin1_memcpy(params->random_seed, state->random_seed, sizeof(mars_kiss64_seed_t));
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_load_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons,
        address_t save_initial_state) {

    neuron_params_t *params = (neuron_params_t *) &address[next];
    for (uint32_t i = 0; i < n_neurons; i++) {
        neuron_model_initialise(&neuron_array[i], &params[i]);
    }

    // If we are to save the initial state, copy the whole of the parameters
    // to the initial state
    if (save_initial_state) {
        spin1_memcpy(save_initial_state, address,
        		n_neurons * sizeof(neuron_params_t));
    }
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_store_neuron_parameters(
        address_t address, uint32_t next, uint32_t n_neurons) {
    neuron_params_t *params = (neuron_params_t *) &address[next];
	for (uint32_t i = 0; i < n_neurons; i++) {
		neuron_model_save_state(&neuron_array[i], &params[i]);
	}
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_add_inputs(
        index_t synapse_type_index, index_t neuron_index,
        input_t weights_this_timestep) {
    // Get the neuron itself
    neuron_impl_t *neuron = &neuron_array[neuron_index];

    // Do something to store the inputs for the next state update
    neuron->inputs[synapse_type_index] += weights_this_timestep;
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_do_timestep_update(
        uint32_t timer_count, uint32_t time, uint32_t n_neurons) {
    for (uint32_t neuron_index = 0; neuron_index < n_neurons; neuron_index++) {
        // Get the neuron itself
        neuron_impl_t *neuron = &neuron_array[neuron_index];

        // If in refractory, count down and spike!
		if (neuron->refract_timer > 0) {
			neuron->refract_timer -= 1;

			// Record things
			neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, ZERO);
			neuron_recording_record_accum(EX_INPUT_INDEX, neuron_index, neuron->inputs[0]);
			neuron_recording_record_accum(IN_INPUT_INDEX, neuron_index, neuron->inputs[1]);

			// Send a spike
			neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);
		    send_spike(timer_count, time, neuron_index);
		    return;
		}

        // Work out the membrane voltage
        REAL v_membrane = neuron->bias + neuron->inputs[0] - neuron->inputs[1];

        // Record things
        neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, v_membrane);
        neuron_recording_record_accum(EX_INPUT_INDEX, neuron_index, neuron->inputs[0]);
        neuron_recording_record_accum(IN_INPUT_INDEX, neuron_index, neuron->inputs[1]);

        // Reset the inputs
        neuron->inputs[0] = ZERO;
        neuron->inputs[1] = ZERO;

        // Just use the integer part of the v_membrane, so we can work in powers of 2
		int32_t v_membrane_int = bitsk(v_membrane) >> 15;

		// Work out the probability of spiking
		uint32_t prob;

		// If the membrane voltage is >= 0, we can left shift (or no shift)
		if (v_membrane_int >= 0) {

			// The probability will overflow (and so be 1) if the bits are going to shift
			// off the end, so then don't bother!
			if ((uint32_t) v_membrane_int <= neuron->max_left_shift) {
				prob = bitsuk(neuron->tau_recip) << v_membrane_int;
			} else {
				prob = 0xFFFFFFFF;
			}
		}

		// If the membrane voltage is negative, we can right shift
		else {
			if ((uint32_t) -v_membrane_int <= neuron->max_right_shift) {
				prob = bitsuk(neuron->tau_recip) >> -v_membrane_int;
			} else {
				prob = 0;
			}
		}

		// Get a random number
		uint32_t random = mars_kiss64_seed(neuron->random_seed);

		// If the random number is less than the probability value, spike
		if (random < prob) {
			neuron->refract_timer = neuron->t_refract - 1;
			neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);
		    send_spike(timer_count, time, neuron_index);
		}
    }
}

#if LOG_LEVEL >= LOG_DEBUG
SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_print_inputs(uint32_t n_neurons) {
    log_debug("-------------------------------------\n");
    for (index_t i = 0; i < n_neurons; i++) {
        neuron_impl_t *neuron = &neuron_array[i];
        log_debug("inputs: %k %k", neuron->inputs[0], neuron->inputs[1]);
    }
    log_debug("-------------------------------------\n");
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static void neuron_impl_print_synapse_parameters(uint32_t n_neurons) {
    // there aren't any accessible
    use(n_neurons);
}

SOMETIMES_UNUSED // Marked unused as only used sometimes
static const char *neuron_impl_get_synapse_type_char(uint32_t synapse_type) {
    if (synapse_type == 0) {
    	return 'E';
    } else if (synapse_type == 1) {
    	return 'I';
    }
    return 'U';
}
#endif // LOG_LEVEL >= LOG_DEBUG


#endif // _MY_FULL_NEURON_IMPL_
