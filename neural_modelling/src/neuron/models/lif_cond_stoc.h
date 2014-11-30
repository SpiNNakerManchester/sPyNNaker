

#ifndef _LIF_COND_NEURON_STOC_
#define _LIF_COND_NEURON_STOC_

#include  "generic_neuron.h"


// define ODE methods and parameters used
#define	RK_METHOD				ode_fix_ss_method_rk4 //ode_fix_ss_method_rk2_v1  // only necessary if not using direct calls
#define	NO_OF_EXPL_FIX_STEPS 1
#define	EXPL_FIX_STEP_SIZE	1.0


/////////////////////////////////////////////////////////////
// definition for LIF neuron
typedef struct neuron_t {

// nominally 'fixed' parameters
	REAL     V_reset;    // post-spike reset membrane voltage    [mV]
	REAL     V_rest;     // membrane resting voltage [mV]
	REAL     R_membrane; // membrane resistance [MegaOhm] 
	
	REAL		V_rev_E;		// reversal voltage - Excitatory    [mV]
	REAL		V_rev_I;		// reversal voltage - Inhibitory    [mV]

// stochastic threshold parameters

    REAL     du_th_inv;     // sensitivity of soft threshold to membrane voltage [mV^(-1)] (inverted in python code)
    REAL     tau_th_inv;    // time constant for soft threshold [ms^(-1)] (inverted in python code)
    REAL     theta;     // soft threshold value  [mV]
	
// variable-state parameter
	REAL     V_membrane; // membrane voltage [mV]

// late entry! Jan 2014 (trickle current)
	REAL		I_offset;	// offset current [nA] but take care because actually 'per timestep charge'
	
// 'fixed' computation parameter - time constant multiplier for closed-form solution
	REAL     exp_TC;        // exp( -(machine time step in ms)/(R * C) ) [.]
	
// for ODE solution only
	REAL  	one_over_tauRC; // [kHz!] only necessary if one wants to use ODE solver because allows * and host double prec to calc - UNSIGNED ACCUM & unsigned fract much slower

// refractory time information
	int32_t refract_timer; // countdown to end of next refractory period [ms/10] - 3 secs limit do we need more? Jan 2014
	int32_t T_refract;  	// refractory time of neuron [ms/10]

    int32_t debug_counter;

} neuron_t;


//
neuron_pointer_t create_lif_cond_stoc_neuron(REAL V_reset, REAL V_rest, REAL V_rev_E, REAL V_rev_I, REAL du_th_inv,
            REAL tau_th_inv, REAL theta, REAL one_over_tauRC, REAL R, int32_t T_refract, REAL V, REAL I, 
            int32_t refract_timer, REAL exp_tc);
					
													
#endif   // include guard

