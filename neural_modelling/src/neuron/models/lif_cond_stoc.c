

#include "lif_cond_stoc.h"

#include "random.h"
#include <stdfix.h>
#include "stdfix-exp.h"

#include <math.h>

#include <debug.h>

// for general machine time steps
static uint32_t	refractory_time_update = 10;  // defaults to 1ms time step i.e. 10 x 1/10ths of a msec

static REAL 		input_this_timestep;  			// used within file scope to send input data around and keep to 4 params

#ifdef USING_ODE_SOLVER

#include "alpha_diff_eq.h"  // only necessary if using ODE updating instead of closed form solution so mainly for testing

// simple Leaky I&F ODE - discrete changes elsewhere
void neuron_ode( REAL t, REAL stateVar[], REAL dstateVar_dt[], neuron_pointer_t neuron ) {

	dstateVar_dt[1] = (( neuron->V_rest - stateVar[1] ) + ( neuron->R_membrane * input_this_timestep )) * neuron->one_over_tauRC;
}

#endif


// setup function which needs to be called in main program before any neuron code executes
// MUST BE: inimum 100, then in 100 steps...
void provide_machine_timestep( uint16_t microsecs ){

	const uint16_t	time_step_divider = 100;

	refractory_time_update = microsecs / time_step_divider;  // 10 for 1ms time step, 1 for 0.1ms time step which is minimum

}


// simple Leaky I&F ODE - discrete changes elsewhere
void lif_neuron_closed_form( neuron_pointer_t neuron, REAL V_prev, int32_t neg_refract_timer_now ) {

	REAL 	alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest,
			this_eTC = neuron->exp_TC;  // this is always the default

//	within-timestep correction for when neuron came out of refractory period
// breaks timestep into thirds - average error from approximation = 1/12th of a timestep

	neuron->V_membrane = 	alpha - this_eTC * ( alpha - V_prev );  // update membrane voltage
}


// ODE solver has just set neuron->V which is current state of membrane voltage
void neuron_discrete_changes( neuron_pointer_t neuron ) {

	neuron->V_membrane = neuron->V_reset;  		// reset membrane voltage

// add to refractory timer takes into account already through period


	neuron->refract_timer  = neuron->T_refract;

}


// .277 ms
bool neuron_state_update( REAL exc_input, REAL inh_input, neuron_pointer_t neuron ) {

	bool spike = false;
	REAL V_last = neuron->V_membrane;

	neuron->refract_timer -= refractory_time_update;  // countdown refractory timer

	if( neuron->refract_timer < 1 ) {  // test for outside refractory time

// exc_input is conductance value from excitatory buffer
// inh_input    "         "       from inhibitory buffer
// we can probably assume that conductances must be positive, and so use unsigned in the buffers for better precision
		input_this_timestep = 	exc_input * ( neuron->V_rev_E - V_last )  +   // need to check units and polarity of inh
										inh_input * ( neuron->V_rev_I - V_last )  +
										neuron->I_offset; // adding offset current - all need to be in nA

		lif_neuron_closed_form( neuron, V_last, -neuron->refract_timer );
//		ode_solve_fix_ss_expl( RK_METHOD, NO_OF_EXPL_FIX_STEPS, EXPL_FIX_STEP_SIZE, neuron );
        
        //stochastic threshold code.
        //begin with random number between 0 and 1
        unsigned long fract r = ulrbits(mars_kiss64_simp());
        
        unsigned fract result;
        accum exponent = (neuron->V_membrane-neuron->theta)*neuron->du_th_inv;
        const unsigned fract prob_saturation = 0.8;
        //if exponent is large, further calculation is unnecessary (result --> prob_saturation).
        if (exponent < 5.0) {
            accum hazard = expk(exponent)*neuron->tau_th_inv;
            result = (1.-expk(-hazard*refractory_time_update))*prob_saturation;
            
        } else {
            result = prob_saturation;
        }
        //io_printf( IO_BUF, "\n %1.6R", result );
        
		spike = REAL_COMPARE( result, >=, r );  // has it spiked?

		if( spike ) {
             neuron->debug_counter++;
             if(neuron->debug_counter > 20) {
                 io_printf( IO_BUF, "\n %02d %11.4k %11.4k", neuron->debug_counter, neuron->V_membrane, result );
                 neuron->debug_counter = 0
             }
             neuron_discrete_changes( neuron );
        }
		}

	return spike;
}


//
void	neuron_set_state( uint8_t i, REAL stateVar[], neuron_pointer_t neuron ) {

	neuron->V_membrane = stateVar[1];
}


//
REAL neuron_get_state( uint8_t i, neuron_pointer_t neuron ) {

	return neuron->V_membrane;  // no need for i in this case leave out switch statement for speed but no range check
}


//
neuron_pointer_t create_lif_cond_stoc_neuron(REAL V_reset, REAL V_rest, REAL V_rev_E, REAL V_rev_I, REAL du_th_inv,
            REAL tau_th_inv, REAL theta, REAL one_over_tauRC, REAL R, int32_t T_refract, REAL V, REAL I, 
            int32_t refract_timer, REAL exp_tc )
{
	neuron_pointer_t neuron = spin1_malloc( sizeof( neuron_t ) );

	neuron->V_membrane = V;	     					io_printf( IO_STD, "\nV membrane    %11.4k mv\n", neuron->V_membrane );
    neuron->theta = theta;
    io_printf( IO_STD, "V thresh (theta)    %11.4k mv\n\n", neuron->theta );
	neuron->V_reset = V_reset;	  					io_printf( IO_STD, "V reset       %11.4k mv\n", neuron->V_reset );
	neuron->V_rest = V_rest;	  					io_printf( IO_STD, "V rest        %11.4k mv\n\n", neuron->V_rest );

	neuron->V_rev_E = V_rev_E;	  					io_printf( IO_STD, "V reversal E   %11.4k mv\n", neuron->V_rev_E );
	neuron->V_rev_I = V_rev_I;	  					io_printf( IO_STD, "V reversal I   %11.4k mv\n\n", neuron->V_rev_I );

    neuron->du_th_inv = du_th_inv;	  				io_printf( IO_STD, "inverse threshold du   %11.4k mv\n", neuron->du_th_inv );
    neuron->tau_th_inv = tau_th_inv;	  			io_printf( IO_STD, "inverse threshold tau   %11.4k mv\n\n", neuron->tau_th_inv );

	neuron->I_offset = I;	     					io_printf( IO_STD, "I offset      %11.4k nA\n", neuron->I_offset );
	neuron->R_membrane = R;	  						io_printf( IO_STD, "R membrane    %11.4k Mohm\n", neuron->R_membrane );
	neuron->one_over_tauRC = one_over_tauRC;	io_printf( IO_STD, "1/tauRC       %11.4k kHz\n", neuron->one_over_tauRC ); // ODE only
	neuron->exp_TC = exp_tc;	  					io_printf( IO_STD, "exp(-ms/(RC)) %11.4k \n\n", neuron->exp_TC );  			// closed-form only

	neuron->T_refract = T_refract;	  			io_printf( IO_STD, "T refract         %u microsecs\n",   neuron->T_refract * 100 );
	neuron->refract_timer = refract_timer;	  	io_printf( IO_STD, "refr timer        %d microsecs\n",   neuron->refract_timer * 100 );

    neuron->debug_counter = 0;

	return neuron;
}


// printout of neuron definition and state variables
void neuron_print( restrict neuron_pointer_t neuron )
{
	log_info( "V membrane    = %11.4k mv", neuron->V_membrane );
	log_info( "V thresh (theta)     = %11.4k mv", neuron->theta );
	log_info( "V reset       = %11.4k mv", neuron->V_reset );
	log_info( "V rest        = %11.4k mv", neuron->V_rest );

    log_info( "inverse threshold du       = %11.4k mv", neuron->du_th_inv );
    log_info( "inverse threshold tau        = %11.4k mv", neuron->tau_th_inv);

	log_info( "V reversal E  = %11.4k mv", neuron->V_rev_E );
	log_info( "V reversal I  = %11.4k mv", neuron->V_rev_I );

	log_info( "I offset      = %11.4k nA", neuron->I_offset );
	log_info( "R membrane    = %11.4k Mohm", neuron->R_membrane );

	log_info( "exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC );

	log_info( "T refract     = %u microsecs", neuron->T_refract * 100 );
}


// access number of state variables, number of parameters & size of the per neuron data structure
void neuron_get_info( uint8_t *num_state_vars, uint16_t *struct_size )
{
	*num_state_vars = 1;
	*struct_size = sizeof( neuron_t );
}
