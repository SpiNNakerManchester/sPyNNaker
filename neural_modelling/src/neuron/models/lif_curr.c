

#include "lif_curr.h"

#include <math.h>

#include <debug.h>

// this is used to set up the eTC array if any TQ is being corrected for, not currently used in production code April 2014
#define TQ_TEST_CODE   \
	#ifdef TEST_0p1   \
		double scale = 0.1;   \
	#else   \
		double scale = 1.0;   \
	#endif   \
	neuron->eTC[0] = (REAL)  exp( -(double)one_over_tauRC * 1.16666667 * scale );   \
	neuron->eTC[1] = (REAL)  exp( -(double)one_over_tauRC * 1.5 * scale );   \
	neuron->eTC[2] = (REAL)  exp( -(double)one_over_tauRC * 1.83333333 * scale );   \
	neuron->exp_TC = (REAL)  exp( -(double)one_over_tauRC * scale );    \
	io_printf( IO_STD, "eTC  %9.5k %9.5k %9.5k \n", neuron->eTC[0], neuron->eTC[1], neuron->eTC[2] );


// for general machine time steps
static uint32_t	refractory_time_update = 10;  // defaults to 1ms time step i.e. 10 x 1/10ths of a msec

static REAL 		input_this_timestep;  			// used within file scope to send input data around and keep to 4 params


#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY

	static uint8_t refract_threshold_correction[3];

#endif
#ifdef SIMPLE_COMBINED_GRANULARITY

	static uint8_t	simple_thresh_update;

#endif


#ifdef USING_ODE_SOLVER

#include "alpha_diff_eq.h"  // only necessary if using ODE updating instead of closed form solution so mainly for testing

// simple Leaky I&F ODE - discrete changes elsewhere
void neuron_ode( REAL t, REAL stateVar[], REAL dstateVar_dt[], neuron_pointer_t neuron ) {

	dstateVar_dt[1] = (( neuron->V_rest - stateVar[1] ) + ( neuron->R_membrane * input_this_timestep )) * neuron->one_over_tauRC;
}

#endif


// setup function which needs to be called in main program before any neuron code executes
// MUST BE: inimum 100, then in 100usec steps...
void provide_machine_timestep( uint16_t microsecs ){

	const uint16_t	time_step_divider = 100;

	refractory_time_update = microsecs / time_step_divider;  // 10 for 1ms time step, 1 for 0.1ms time step which is minimum

#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
	io_printf( IO_STD, "\n *** Refractory granularity correction \n" );

#endif
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY
	io_printf( IO_STD, "\n *** Threshold granularity correction \n" );

	refract_threshold_correction[0] = (uint8_t) round( (double)refractory_time_update * 0.16667 );
	refract_threshold_correction[1] = (uint8_t) round( (double)refractory_time_update * 0.50000 );
	refract_threshold_correction[2] = (uint8_t) round( (double)refractory_time_update * 0.83333 );

	io_printf( IO_STD, "\n refractory updates  %u %u %u \n",
							refract_threshold_correction[0], refract_threshold_correction[1], refract_threshold_correction[2] );
#endif
#ifdef SIMPLE_COMBINED_GRANULARITY
	io_printf( IO_STD, "\n *** Simple combined granularity correction \n" );

	simple_thresh_update = refractory_time_update / 2;   // nasty integer divide lets hope it's an even number always!

	io_printf( IO_STD, "\n refractory_time_update  %u   simp thresh update %u  \n", refractory_time_update, simple_thresh_update );
#endif

}


// simple Leaky I&F ODE - discrete changes elsewhere -  assumes 1ms timestep?
void lif_neuron_closed_form( neuron_pointer_t neuron, REAL V_prev, int32_t neg_refract_timer_now ) {

	REAL 	alpha = input_this_timestep * neuron->R_membrane + neuron->V_rest,
			this_eTC = neuron->exp_TC;  // this is always the default

//	within-timestep correction for when neuron came out of refractory period
// breaks timestep into thirds - average error from approximation = 1/12th of a timestep
#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY
//io_printf( IO_STD, " ref time %d  ", neg_refract_timer_now );

	if( neg_refract_timer_now < refractory_time_update ) { // only used if it just came out of refractory period this timestep

// so set extra length of time for membrane voltage to develop according to when it came out of ref period
		if( neg_refract_timer_now < neuron->ref_divisions[0] ) 			// came out at end of timestep
			this_eTC = neuron->eTC[0];

		else if( neg_refract_timer_now > neuron->ref_divisions[1] )   // came out at start of timestep
			this_eTC = neuron->eTC[2];

		else
			this_eTC = neuron->eTC[1];												// otherwise assume in middle third

//		io_printf( IO_STD, " ref time %d  eTC  %9.5k \n", neg_refract_timer_now, this_eTC );

		}
#endif
#ifdef SIMPLE_COMBINED_GRANULARITY  // only used if it just came out of refractory period this timestep

	if( neg_refract_timer_now < refractory_time_update ) this_eTC = neuron->eTC[1];

#endif

	neuron->V_membrane = 	alpha - this_eTC * ( alpha - V_prev );  // update membrane voltage
}


// ODE solver has just set neuron->V which is current state of membrane voltage
void neuron_discrete_changes( neuron_pointer_t neuron ) {

	neuron->V_membrane = neuron->V_reset;  		// reset membrane voltage

// add to refractory timer takes into account already through period
#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY

	neuron->refract_timer  = ( neuron->T_refract - refract_threshold_correction[ neuron->prev_spike_code ] );

//	io_printf( IO_STD, " code  %u  thresh ref update %u \n", neuron->prev_spike_code, neuron->T_refract - refract_threshold_correction[neuron->prev_spike_code] );

#else  // one of the simpler ones
#ifdef SIMPLE_COMBINED_GRANULARITY

	neuron->refract_timer  = neuron->T_refract - simple_thresh_update;  // Expected value of refractory time lost in timestep
#else

	neuron->refract_timer  = neuron->T_refract;   // reset refractory timer
#endif

#endif  // the more complex one
}


// .277 ms
bool neuron_state_update( REAL exc_input, REAL inh_input, REAL external_bias, neuron_pointer_t neuron ) {

	bool spike = false;
	REAL V_last = neuron->V_membrane;

	neuron->refract_timer -= refractory_time_update;  // countdown refractory timer

	if( neuron->refract_timer < 1 ) {  // test for outside refractory time

		input_this_timestep = exc_input - inh_input + external_bias + neuron->I_offset; // now adding offset current - all need to be in nA

		lif_neuron_closed_form( neuron, V_last, -neuron->refract_timer );
//		ode_solve_fix_ss_expl( RK_METHOD, NO_OF_EXPL_FIX_STEPS, EXPL_FIX_STEP_SIZE, neuron );
//	   ode_solve_fix_ss_expl_rk2_v1( NO_OF_EXPL_FIX_STEPS, EXPL_FIX_STEP_SIZE, neuron );

		spike = REAL_COMPARE( neuron->V_membrane, >=, neuron->V_thresh );  // has it spiked?

#ifdef CORRECT_FOR_THRESHOLD_GRANULARITY

		if( spike ) {

			REAL A, B, thresh;

// calculate the two simple linear indicators of where the threshold was cut
			thresh = neuron->V_thresh;

			A = neuron->V_membrane - thresh;
			B = thresh - V_last;

			if			( A >= 2*B ) 	neuron->prev_spike_code = 2; 	// it spiked in first third
			else if  ( B >= 2*A ) 	neuron->prev_spike_code = 0;	// it spiked in last third
			else						 	neuron->prev_spike_code = 1; 	// it spiked near middle

//			io_printf( IO_STD, " A %9.4k   B %9.4k  code %u \n", A, B, neuron->prev_spike_code );

			neuron_discrete_changes( neuron );
			}

#else  // works for both no correction and simple correction case
		if( spike ) neuron_discrete_changes( neuron );
#endif
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
neuron_pointer_t create_lif_neuron(
			REAL V_thresh, REAL V_reset, REAL V_rest, REAL one_over_tauRC,
			REAL R, int32_t T_refract, REAL V, REAL I, int32_t refract_timer, REAL exp_tc )
{
	neuron_pointer_t neuron = spin1_malloc( sizeof( neuron_t ) );

	neuron->V_membrane = V;	     					io_printf( IO_STD, "\nV membrane    %11.4k mv\n", neuron->V_membrane );
	neuron->V_thresh = V_thresh;  				io_printf( IO_STD, "V thresh      %11.4k mv\n", neuron->V_thresh );
	neuron->V_reset = V_reset;	  					io_printf( IO_STD, "V reset       %11.4k mv\n", neuron->V_reset );
	neuron->V_rest = V_rest;	  					io_printf( IO_STD, "V rest        %11.4k mv\n\n", neuron->V_rest );

	neuron->I_offset = I;	     					io_printf( IO_STD, "I offset      %11.4k nA?\n", neuron->I_offset );
	neuron->R_membrane = R;	  						io_printf( IO_STD, "R membrane    %11.4k Mohm\n", neuron->R_membrane );
	neuron->one_over_tauRC = one_over_tauRC;	io_printf( IO_STD, "1/tauRC       %11.4k kHz\n", neuron->one_over_tauRC ); // ODE only
	neuron->exp_TC = exp_tc;	  					io_printf( IO_STD, "exp(-ms/(RC)) %11.4k \n\n", neuron->exp_TC );  			// closed-form only

	neuron->T_refract = T_refract;	  			io_printf( IO_STD, "T refract         %u microsecs\n",   neuron->T_refract * 100 );
	neuron->refract_timer = refract_timer;	  	io_printf( IO_STD, "refr timer        %d microsecs\n",   neuron->refract_timer * 100 );

#ifdef CORRECT_FOR_REFRACTORY_GRANULARITY  // only works properly for 1000, 700, 400 microsec timesteps

	neuron->ref_divisions[0] = (uint8_t) round( (refractory_time_update-1) /* ms/10 */ * 0.33333 );  // so only works down to 300 microsec timesteps
	neuron->ref_divisions[1] = (uint8_t) round( (refractory_time_update-1) /* ms/10 */ * 0.66667 );

	io_printf( IO_STD, "NRF  %d  %d \n", neuron->ref_divisions[0], neuron->ref_divisions[1] );

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


// printout of neuron definition and state variables
void neuron_print( restrict neuron_pointer_t neuron )
{
	log_info( "V membrane    = %11.4k mv", neuron->V_membrane );
	log_info( "V thresh      = %11.4k mv", neuron->V_thresh );
	log_info( "V reset       = %11.4k mv", neuron->V_reset );
	log_info( "V rest        = %11.4k mv", neuron->V_rest );

	log_info( "I offset      = %11.4k nA", neuron->I_offset );
	log_info( "R membrane    = %11.4k Mohm", neuron->R_membrane );

	log_info( "exp(-ms/(RC)) = %11.4k [.]", neuron->exp_TC );

	log_info( "T refract     = %u microsecs", neuron->T_refract * 100 );
}


// access number of state variables, number of parameters & size of the per neuron data structure
void neuron_get_info( uint8_t *num_state_vars, /* uint8_t *num_params, */ uint16_t *struct_size )
{
	*num_state_vars = 1;
	*struct_size = sizeof( neuron_t );
}

