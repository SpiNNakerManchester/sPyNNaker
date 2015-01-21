

#ifndef _LIF_CURR_NEURON_
#define _LIF_CURR_NEURON_

#include  "generic_neuron.h"


// define ODE methods and parameters used
#define	RK_METHOD				ode_fix_ss_method_rk2_v1  // only necessary if not using direct calls
#define	NO_OF_EXPL_FIX_STEPS 1
#define	EXPL_FIX_STEP_SIZE	1.0

//#define CORRECT_FOR_REFRACTORY_GRANULARITY  // only works properly for 1000, 700, 400 microsec timesteps
//#define CORRECT_FOR_THRESHOLD_GRANULARITY
//#define SIMPLE_COMBINED_GRANULARITY   // 9% slower than standard but inevitably more accurate(?) might over-compensate

//#define	TEST_0p1


/////////////////////////////////////////////////////////////
// definition for LIF neuron
typedef struct neuron_t {

// nominally 'fixed' parameters
	REAL     V_thresh;   // membrane voltage threshold at which neuron spikes [mV]
	REAL     V_reset;    // post-spike reset membrane voltage    [mV]
	REAL     V_rest;     // membrane resting voltage [mV]
	REAL     R_membrane; // membrane resistance [some multiplier of Ohms, TBD probably MegaOhm] 

// variable-state parameter
	REAL     V_membrane;    // membrane voltage [mV]

// late entry! Jan 2014 (trickle current)
	REAL		I_offset;		// offset current [nA] but take care because actually 'per timestep charge'
	
// 'fixed' computation parameter - time constant multiplier for closed-form solution
	REAL     exp_TC;        // exp( -(machine time step in ms)/(R * C) ) [.]
	
// for ODE solution only
	REAL  	one_over_tauRC; // [kHz!] only necessary if one wants to use ODE solver because allows * and host double prec to calc - UNSIGNED ACCUM & unsigned fract much slower

// refractory time information
	int32_t refract_timer; // countdown to end of next refractory period [ms/10] - 3 secs limit do we need more? Jan 2014
	int32_t T_refract;  	// refractory time of neuron [ms/10]

#ifdef SIMPLE_COMBINED_GRANULARITY
	REAL		eTC[3];				// store the 3 internal timestep to avoid granularity
#endif
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
	uint8_t	prev_spike_code;  // which period previous spike happened to approximate threshold crossing
	REAL		eTC[3];				// store the 3 internal timestep to avoid granularity
#endif
#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
	uint8_t	ref_divisions[2];	// approx corrections for release from refractory period
	REAL		eTC[3];				// store the 3 internal timestep to avoid granularity
#endif

} neuron_t;


//
neuron_pointer_t create_lif_neuron(  REAL V_thresh, REAL V_reset, REAL V_rest, REAL one_over_tauRC, REAL R,
													int32_t T_refract, REAL V, REAL I, int32_t refract_timer, REAL exp_tc );
					
													
#endif   // include guard

