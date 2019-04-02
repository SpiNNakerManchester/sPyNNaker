#ifndef _ADDITIONAL_INPUT_GEN_ION_CH_CURRENT_
#define _ADDITIONAL_INPUT_GEN_ION_CH_CURRENT_

#include "additional_input.h"
#include "sqrt.h"

#include <debug.h>

#define TIMESTEP 0.100006103515625k
#define NUM_CURRENTS 1
input_t currents[NUM_CURRENTS];

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

typedef struct ion_current {
	accum I_ion;
	accum g;
	accum E;
	uint32_t N;

	accum m; // activation
	accum m_pow;
	accum m_inf;
	accum tau_m
	accum e_to_t_on_tau_m;

	accum h; // inactivation
	accum h_inf;
	accum tau_h;
	accum e_to_t_on_tau_h;
};

typedef struct additional_input_t {
	ion_current ion_ch;
} additional_input_t;

static inline void _print_additional_input_params(
		additional_input_t* additional_input) {

}

static input_t* additional_input_get_input_value_as_current(
		additional_input_pointer_t additional_input, state_t membrane_voltage) {

	// Update gating parameters m_inf, h_inf, e_to_t_on_tau_m, e_to_t_on_tau_h
	additional_input.ion_ch.tau_m = 1 / (alpha(V) + beta(V)); // expand functions
	additional_input.ion_ch.tau_h = 1 / (alpha(V) + beta(V)); // expand functions

	additional_input.ion_ch.m_inf = 1 / (alpha(V) + beta(V)); // expand functions
	additional_input.ion_ch.h_inf = 1 / (alpha(V) + beta(V)); // expand functions

	// Update model
	additional_input.ion_ch.e_to_t_on_tau_m = exp(
			additional_input.ion_ch.tau_m);
	additional_input.ion_ch.e_to_t_on_tau_h = exp(
			additional_input.ion_ch.tau_h);

	additional_input.ion_ch.m = additional_input.ion_ch.m_inf
			+ (additional_input.ion_ch.m - additional_input.ion_ch.m_inf)
					* additional_input.ion_ch.e_to_t_on_tau_m;

	additional_input.ion_ch.h = additional_input.ion_ch.h_inf
			+ (additional_input.ion_ch.h - additional_input.ion_ch.h_inf)
					* additional_input.ion_ch.e_to_t_on_tau_h;

	// Raise to power N
	additional_input.ion_ch.m_pow = additional_input.ion_ch.m;
	for (int i = 0; i < additional_input.ion_ch.N; i++) {
		additional_input.ion_ch.m_pow = additional_input.ion_ch.m;
	}

	additional_input.ion_ch.I_ion = additional_input.ion_ch.g
			* additional_input.ion_ch.m_pow * additional_input.ion_ch.h
			* (membrane_voltage - additional_input.ion_ch.E);

	currents[0] = additional_input.ion_ch.I_ion;

	return &currents[0];

}

static void additional_input_has_spiked(
		additional_input_pointer_t additional_input) {
	// Do nothing.
	use(additional_input);
}

#endif // _ADDITIONAL_INPUT_GEN_ION_CH_CURRENT_
