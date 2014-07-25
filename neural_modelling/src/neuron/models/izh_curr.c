

#include "izh_curr.h"

#include <debug.h>


static REAL input_this_timestep;  // used with file static scope to send input data around

static REAL machine_timestep = REAL_CONST( 1.0 );  // in msecs

static const REAL V_threshold = REAL_CONST( 30.0 );

static const REAL SIMPLE_TQ_OFFSET = REAL_CONST( 1.85 );


/////////////////////////////////////////////////////////////
// definition for Izhikevich neuron
void neuron_ode( REAL t, REAL stateVar[], REAL dstateVar_dt[], neuron_pointer_t neuron ) {

	REAL V_now = stateVar[1], U_now = stateVar[2];
//io_printf( IO_BUF, " sv1 %9.4k  V %9.4k --- sv2 %9.4k  U %9.4k\n", stateVar[1], neuron->V, stateVar[2], neuron->U );

	dstateVar_dt[1] = REAL_CONST(140.0) + (REAL_CONST(5.0) + REAL_CONST(0.0400) * V_now) * V_now - U_now + input_this_timestep; // V
	dstateVar_dt[2] = neuron->A * ( neuron->B * V_now - U_now );  // U
}


// setup function which needs to be called in main program before any neuron code executes
// minimum 100, then in 100 steps...
void provide_machine_timestep( uint16_t microsecs ){

	const double	time_step_multiplier = 0.00100;

	machine_timestep = (REAL)( microsecs * time_step_multiplier );
}


/*
		best balance between speed and accuracy so far from ODE solve comparison work
*/
void rk2_kernel_midpoint( REAL h, neuron_pointer_t neuron ) {

	REAL 	lastV1 = neuron->V, lastU1 = neuron->U, a = neuron->A, b = neuron->B;  // to match Mathematica names

	REAL	pre_alph = REAL_CONST(140.0) + input_this_timestep - lastU1,
			alpha = pre_alph + ( REAL_CONST(5.0) + REAL_CONST(0.0400) * lastV1 ) * lastV1,
			eta = lastV1 + REAL_HALF( h * alpha ),
			beta = REAL_HALF( h * ( b * lastV1 - lastU1 ) * a ); // could be represented as a long fract?

//	neuron->V = lastV1 +
	neuron->V +=
					h * ( pre_alph - beta + ( REAL_CONST(5.0) + REAL_CONST(0.0400) * eta ) * eta );

//	neuron->U = lastU1 +
	neuron->U +=
					a * h * ( -lastU1 - beta + b * eta );
}


// ODE solver has just set neuron->V which is current state of membrane voltage
void neuron_discrete_changes( neuron_pointer_t neuron ) {

   neuron->V  = neuron->C;    // reset membrane voltage
	neuron->U += neuron->D;		// offset 2nd state variable
}


//
bool neuron_state_update( REAL exc_input, REAL inh_input, neuron_pointer_t neuron ) {

	input_this_timestep = exc_input - inh_input + neuron->I_offset; 	// all need to be in nA

	rk2_kernel_midpoint( neuron->this_h, neuron );  						// the best AR update so far

	bool spike = REAL_COMPARE( neuron->V, >=, V_threshold );

	if( spike ) {
		neuron_discrete_changes( neuron );
		neuron->this_h = machine_timestep * SIMPLE_TQ_OFFSET; //REAL_CONST( 1.85 );  // simple threshold correction - next timestep (only) gets a bump
		}
	else
		neuron->this_h = machine_timestep;

	return spike;
}


//
void	neuron_set_state( uint8_t i, REAL stateVar[], neuron_pointer_t neuron ) {

	neuron->V = stateVar[1];
	neuron->U = stateVar[2];
}


//
REAL neuron_get_state( uint8_t i, neuron_pointer_t neuron ) {

	switch ( i ) {
		case  1: return neuron->V;
		case  2: return neuron->U;
		}
}


//
neuron_pointer_t create_izh_neuron(  REAL A, REAL B, REAL C, REAL D, REAL V, REAL U, REAL I )
{
	neuron_pointer_t neuron = spin1_malloc( sizeof( neuron_t ) );

	neuron->A = A;  io_printf( WHERE_TO, "\nA = %11.4k \n", neuron->A );
	neuron->B = B;  io_printf( WHERE_TO, "B = %11.4k \n", neuron->B );
	neuron->C = C;  io_printf( WHERE_TO, "C = %11.4k mV\n", neuron->C );
	neuron->D = D;  io_printf( WHERE_TO, "D = %11.4k ??\n\n", neuron->D );

	neuron->V = V;  io_printf( WHERE_TO, "V = %11.4k mV\n", neuron->V );
	neuron->U = U;  io_printf( WHERE_TO, "U = %11.4k ??\n\n", neuron->U );

	neuron->I_offset = I;  io_printf( WHERE_TO, "I = %11.4k nA?\n", neuron->I_offset );

	neuron->this_h = machine_timestep * REAL_CONST(1.001);  io_printf( WHERE_TO, "h = %11.4k ms\n", neuron->this_h );

	return neuron;
}


// printout of neuron definition and state variables
void neuron_print( restrict neuron_pointer_t neuron )
{
	log_info( "A = %11.4k ", neuron->A );
	log_info( "B = %11.4k ", neuron->B );
	log_info( "C = %11.4k ", neuron->C );
	log_info( "D = %11.4k ", neuron->D );

	log_info( "V = %11.4k ", neuron->V );
	log_info( "U = %11.4k ", neuron->U );

	log_info( "I = %11.4k \n", neuron->I_offset );
}


// access number of state variables, number of parameters & size of the per neuron data structure
void neuron_get_info( uint8_t *num_state_vars, uint16_t *struct_size )
{
	*num_state_vars = 2;
	*struct_size = sizeof( neuron_t );
}

