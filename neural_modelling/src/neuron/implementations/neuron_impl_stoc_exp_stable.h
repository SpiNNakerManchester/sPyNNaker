/*
 * Copyright (c) 2023 The University of Manchester
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

//! \file
//! \brief Stochastic neuron implementation with exponential probability

#ifndef _NEURON_IMPL_STOC_EXP_
#define _NEURON_IMPL_STOC_EXP_

#include <neuron/implementations/neuron_impl.h>
#include <spin1_api.h>
#include <debug.h>
#include <random.h>
#include <stdfix-full-iso.h>
#include <common/maths-util.h>

#define V_RECORDING_INDEX 0
#define EX_INPUT_INDEX 1
#define IN_INPUT_INDEX 2
#define PROB_INDEX 3
#define N_RECORDED_VARS 4

#define SPIKE_RECORDING_BITFIELD 0
#define N_BITFIELD_VARS 1

#include <neuron/neuron_recording.h>

#include <neuron/current_sources/current_source_impl.h>
#include <neuron/current_sources/current_source.h>

//! definition of neuron parameters
typedef struct neuron_params_t {

	//! The initial membrane voltage
	REAL v_init;

	//! The reset membrane voltage after a spike
	REAL v_reset;

    //! The tau value of the neuron, multiplied by 2^v to get probability
    UREAL tau;

    //! The refractory period of the neuron in milliseconds
    UREAL tau_refract;

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

	//! The membrane voltage
	REAL v_membrane;

	//! The reset voltage after a spike
	REAL v_reset;

    //! The tau value of the neuron
    UREAL tau;

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

static inline uint64_t multiply(uint64_t a, uint32_t b) {
	return ((a >> 32) * (uint64_t) b) + (((a & 0xFFFFFFFFL) * (uint64_t) b) >> 32);
}

//! The minimum value of tau that has the potential to reduce below 1 from
//! mulitplication by negative fractional power of 2 of 16 or less.  In other
//! words, if tau is bigger than this, no multiplication by fractional negative
//! powers of 2 will ever bring it below 1, so a probability of >=1 is guaranteed.
static const uint32_t MIN_TAU = 0x10B55;

//! \brief Calculates the probability as a uint32_t from 0 to 0xFFFFFFFF (which is 1)
static inline uint32_t get_probability(UREAL tau, REAL p) {

	if (p >= 0) {

		// If tau is already more than 1, it will never get smaller here,
		// so just immediately return a probability of "1"
		if (tau >= 1.0k) {
			return 0xFFFFFFFF;
		}

		// The amount of left shift that will result in a tau > 1 (where tau
		// is 16-bits integer, 16-bits fractional, and < 1.0k, so we expect
		// at least 16 leading zeros, thus this can only be >= 0).  Note a
		// a 1 at bit 16 means clz = 16, but we can shift 1 place before >= 1
		// so we subtract 15 from clz to get the right number.
	    uint32_t over_left_shift = __builtin_clz(bitsuk(tau)) - 15;

		// If tau is going to be shifted by this amount
		if (p >= over_left_shift) {
			return 0xFFFFFFFF;
		}

		// Shift left by integer part to perform power of 2
		uint64_t accumulator = ((uint64_t) bitsuk(tau)) << (bitsk(p) >> 15);
		uint32_t fract_bits = bitsk(p) & 0x7FFF;

		// Multiply in fractional powers for each non-zero fractional bits
		for (uint32_t i = 0; i < 15; i++) {
			uint32_t bit = (fract_bits >> (14 - i)) & 0x1;
			if (bit) {
				// Do a U1616 * U1616 multiply here, which is safe in 64-bits
				accumulator = (accumulator * fract_powers_2[i]) >> 16;

				// If we are >= 1, return now as won't get smaller
				if (accumulator >= bitsuk(1.0ulk)) {
					return 0xFFFFFFFF;
				}
			}
		}

	    // Multiply accumulated fraction (must be <= 1 here) by 0xFFFFFFFF
		// to get final answer
		return (uint32_t) ((accumulator * 0xFFFFFFFFL) >> 16);
	} else {
		// If tau is too big, we will never make it small enough with negative
		// powers, so just return probability of 1
		if (bitsuk(tau) > MIN_TAU) {
			return 0xFFFFFFFF;
		}

	    // Negative left shift = positive right shift; have to multiply here
		// as accum negating seems to fail!
		REAL val = p * REAL_CONST(-1);

		// The amount of right shift that will make the MSB of tau disappear,
		// and so the value will be 0.  The most number of leading zeros is 32,
		// so this is always >= 0.  If we have a bit in position 31 (a very big
		// tau), this clz = 0 so this is 32, which means we can shift by 32
		uint32_t over_right_shift = 32 - __builtin_clz(bitsuk(tau));

		// If p <= 0, tau can only get smaller through multiplication with
		// fractional powers, so there is no point in doing the calculation if
		// it will already be shifted out of range of an accum
		if (val >= over_right_shift) {
			return 0;
		}

		// Shift right by integer value to perform negative power of 2
		uint64_t accumulator = ((uint64_t) bitsuk(tau)) >> (bitsk(val) >> 15);
		uint32_t fract_bits = bitsk(val) & 0x7FFF;

		// Multiply in fractional powers for each non-zero fractional bits
		for (uint32_t i = 0; i < 15; i++) {
			uint32_t bit = (fract_bits >> (14 - i)) & 0x1;
			if (bit) {
				// Do a U1616 * U1616 multiply here
				accumulator = (accumulator * fract_powers_half[i]) >> 16;

				// If we have reached a value of 0, return
				if (accumulator == 0) {
					return 0;
				}
			}
		}

		// Multiply accumulated fraction (must be <= 1 here) by 0xFFFFFFFF
		// to get final answer
		return (uint32_t) ((accumulator * 0xFFFFFFFFL) >> 16);
	}
}

static inline void neuron_model_initialise(
		neuron_impl_t *state, neuron_params_t *params) {
	state->v_membrane = params->v_init;
	state->v_reset = params->v_reset;
	UREAL ts = params->time_step;
	state->tau = params->tau;
	state->bias = params->bias;
	state->t_refract = stoc_exp_ceil_accum(ukdivuk(params->tau_refract, ts));
    state->refract_timer = params->refract_init;
    spin1_memcpy(state->random_seed, params->random_seed, sizeof(mars_kiss64_seed_t));
    validate_mars_kiss64_seed(state->random_seed);

    // Reset the inputs
    state->inputs[0] = ZERO;
    state->inputs[1] = ZERO;
}

static inline void neuron_model_save_state(neuron_impl_t *state, neuron_params_t *params) {
	params->v_init = state->v_membrane;
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
			neuron_recording_record_int32(PROB_INDEX, neuron_index, 0);
			neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, neuron->v_membrane);
			neuron_recording_record_accum(EX_INPUT_INDEX, neuron_index, neuron->inputs[0]);
			neuron_recording_record_accum(IN_INPUT_INDEX, neuron_index, neuron->inputs[1]);

			// Reset the inputs
			neuron->inputs[0] = ZERO;
			neuron->inputs[1] = ZERO;

			// Send a spike
			neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);
		    send_spike(timer_count, time, neuron_index);
		    continue;
		}

        // Work out the membrane voltage
        neuron->v_membrane += (neuron->bias + neuron->inputs[0]) - neuron->inputs[1];

        // Record things
        neuron_recording_record_accum(V_RECORDING_INDEX, neuron_index, neuron->v_membrane);
        neuron_recording_record_accum(EX_INPUT_INDEX, neuron_index, neuron->inputs[0]);
        neuron_recording_record_accum(IN_INPUT_INDEX, neuron_index, neuron->inputs[1]);

        // Reset the inputs
        neuron->inputs[0] = ZERO;
        neuron->inputs[1] = ZERO;

        // Work out the probability
        uint32_t prob = get_probability(neuron->tau, neuron->v_membrane);

		// Record the probability
		neuron_recording_record_int32(PROB_INDEX, neuron_index, (int32_t) prob);

		// Get a random number
		uint32_t random = mars_kiss64_seed(neuron->random_seed);

		// If the random number is less than the probability value, spike
		if (random < prob) {
			neuron->v_membrane = neuron->v_reset;
			neuron->refract_timer = neuron->t_refract - 1;
			neuron_recording_record_bit(SPIKE_RECORDING_BITFIELD, neuron_index);
		    send_spike(timer_count, time, neuron_index);
		}

		if (neuron->v_membrane < neuron->v_reset) {
			neuron->v_membrane = neuron->v_reset;
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


#endif // _NEURON_IMPL_STOC_EXP_
