#ifndef _ADDITIONAL_INPUT_ALL_CURRENTS_
#define _ADDITIONAL_INPUT_ALL_CURRENTS_

#include "additional_input.h"
#include "sqrt.h"

#include <debug.h>

#define TIMESTEP 0.100006103515625k
#define NUM_CURRENTS 4
input_t currents[NUM_CURRENTS];

// Define some multiplication with rounding routines
// ---------------------------------------------------------------------------

#define MULT_ROUND_NEAREST_ACCUM(x,y) 										\
    ({                            											\
    __typeof__(x) temp0 = (x);		    									\
    __typeof__(y) temp1 = (y);												\
    REAL result;															\
    if (__builtin_types_compatible_p(__typeof__(x), s1615) && 				\
        __builtin_types_compatible_p(__typeof__(y), s1615)) { 				\
        result =  (kbits(__stdfix_smul_k_round_nearest(bitsk(temp0),		\
                  bitsk(temp1)))); 											\
    } else if ((__builtin_types_compatible_p(__typeof__(x), s1615) && 		\
               __builtin_types_compatible_p(__typeof__(y), s031)))  { 		\
        result =  (accum_times_long_fract_nearest(temp0, temp1)); 			\
    } else if (__builtin_types_compatible_p(__typeof__(x), s031) && 		\
               __builtin_types_compatible_p(__typeof__(y), s1615)) {  		\
        result = (accum_times_long_fract_nearest(temp1, temp0)); 			\
    } else if ((__builtin_types_compatible_p(__typeof__(x), s1615) && 		\
               __builtin_types_compatible_p(__typeof__(y), u032)))  { 		\
        result =  (accum_times_u_long_fract_nearest(temp0, temp1)); 		\
    } else if (__builtin_types_compatible_p(__typeof__(x), u032) && 		\
               __builtin_types_compatible_p(__typeof__(y), s1615)) {  		\
        result = (accum_times_u_long_fract_nearest(temp1, temp0)); 			\
    } else { 																\
    } 																		\
    result; 																\
    })

// Multiply two integer representations of accum and return an integer
// representation of an accum answer, rounded to nearest accum.
static inline int32_t __stdfix_smul_k_round_nearest(
    int32_t x,
    int32_t y)
{
    if (x == INT32_MIN && y == INT32_MIN) { // special case for -1.0*-1.0
        return INT32_MAX;
    }

    return __stdfix_sat_k(__stdfix_round_s64(
		(__I64(x) * __I64(y)), 15) >> 15);
}

// Multiply an accum and a signed long fract and return an accum answer rounded
// to the nearest accum.
static inline accum accum_times_long_fract_nearest ( accum x, long fract y )
{
    register int64_t r;

    r = (int64_t)(bitsk (x)) * (int64_t)(bitslr (y));

    return (kbits (((int32_t)(r >> 31) + ((int32_t)(r >> 30) & 1))));
}

// Multiply accum and an unsigned long fract and return an accum answer rounded
// to the nearest accum.
static inline accum accum_times_u_long_fract_nearest ( accum x, unsigned long fract y )
{
    register int64_t r;

    r = (int64_t)(bitsk (x)) * (uint64_t)(bitsulr (y));

    return (kbits (((int32_t)(r >> 32) + ((int32_t)(r >> 31) & 1))));
}

//----------------------------------------------------------------------------

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

typedef struct additional_input_t {
    // Pacemaker Current
    accum    I_H;
    accum    g_H;         // max pacemaker conductance
    accum    E_H;         // reversal potential
    accum    m_H;
    accum    m_inf_H;
    accum    e_to_t_on_tau_m_H;
    // Calcium Current
    accum    I_T;
    accum    g_T;         // max pacemaker conductance
    accum    E_T;         // reversal potential
    accum    m_T;
    accum    m_inf_T;
    accum    e_to_t_on_tau_m_T;
    accum    h_T;
    accum    h_inf_T;
    accum    e_to_t_on_tau_h_T;
    // Sodium Current
    accum    I_NaP;
    accum    g_NaP;       // max sodium conductance
    accum    E_NaP;       // sodium reversal potential
    accum    m_inf_NaP;
    // Potassium Current
    accum    I_DK;
    accum    g_DK;        // max potassium conductance
    accum    E_DK;        // potassium reversal potential
    accum    m_inf_DK;
    accum    e_to_t_on_tau_m_DK;
    accum    D;           // instead of h_DK
    accum    D_influx;  // instead of h_inf_DK
    // Voltage Clamp
    accum      v_clamp;    // voltage for voltage clamp [mV], hold voltage is just V_rest
    uint32_t  s_clamp;    // clamp starting time [timesteps]
    uint32_t  t_clamp;    // clamp duration [timesteps]
    //TODO:  maybe more efficient to get dt from other part of the software?
    accum    dt;
} additional_input_t;

//// Variables to control 'patch clamp' tests
//static input_t local_v;



static inline void _print_additional_input_params(additional_input_t* additional_input){

                 io_printf(IO_BUF, "Pacemaker Current \n"
                       "     I_H: %k, g_H: %k, E_H: %k,   \n"
                       "     m_H: %k,m_inf_H: %k,e_to_t_on_tau_m_H: %k, \n"
                       "Calcium Current: \n"
                       "    I_T: %k, g_T: %k, E_T: %k,\n"
                       "    m_T: %k,m_inf_T: %k, e_to_t_on_tau_m_T: %k,\n"
                       "    h_T: %k, h_inf_T: %k, e_to_t_on_tau_h_T: %k,\n"
                       "Sodium Current:  \n"
                       "    I_NaP: %k, g_NaP: %k,E_NaP: %k,\n"
                       "    m_inf_NaP: %k,\n"
                       "Potassium Current:   \n"
                       "    I_DK: %k, g_DK: %k, E_DK: %k, \n"
                       "     m_inf_DK: %k,e_to_t_on_tau_m_DK: %k,\n"
                       "     D: %k, D_infinity: %k,\n"
                       "Voltage Clamp:      \n"
                       "     v_clamp: %k, s_clamp: %k, t_clamp: %k, dt: %k\n\n",
                       // Pacemaker Current
                       additional_input->I_H,
                       additional_input->g_H,
                       additional_input->E_H,
                       additional_input->m_H,
                       additional_input->m_inf_H,
                       additional_input->e_to_t_on_tau_m_H,
                       // Calcium Current
                       additional_input->I_T,
                       additional_input->g_T,
                       additional_input->E_T,
                       additional_input->m_T,
                       additional_input->m_inf_T,
                       additional_input->e_to_t_on_tau_m_T,
                       additional_input->h_T,
                       additional_input->h_inf_T,
                       additional_input->e_to_t_on_tau_h_T,
                       // Sodium Current
                       additional_input->I_NaP,
                       additional_input->g_NaP,
                       additional_input->E_NaP,
                       additional_input->m_inf_NaP,
                       // Potassium Current
                       additional_input->I_DK,
                       additional_input->g_DK,
                       additional_input->E_DK,
                       additional_input->m_inf_DK,
                       additional_input->e_to_t_on_tau_m_DK,
                       additional_input->D,
                       additional_input->D_influx,
                       // Voltage Clamp
                       additional_input->v_clamp,
                       additional_input->s_clamp,
                       additional_input->t_clamp,
                       additional_input->dt);
}

static input_t* additional_input_get_input_value_as_current(
        additional_input_pointer_t additional_input,
        state_t membrane_voltage) {

//		if (n_dt >= additional_input->s_clamp &&
//            n_dt < additional_input->s_clamp + additional_input->t_clamp){
//         // local_v +=1;
//         // membrane_voltage = local_v;
//            local_v = additional_input->v_clamp;
//        } else {
//            local_v = -65k;
//        }

//        membrane_voltage = local_v;

        // log_info("membrane potential: %k", membrane_voltage);

//	_print_additional_input_params(additional_input);

//------------------------------------------------------------------------
//    profiler_write_entry_disable_irq_fiq(
//        PROFILER_ENTER | PROFILER_INTRINSIC_CURRENT);
//------------------------------------------------------------------------
        // Pacemaker Current.

        additional_input->m_inf_H = 1k / (1k + expk((membrane_voltage+75k)/5.5k)); // this divide can be switched to multiply

        additional_input->e_to_t_on_tau_m_H =
                  expk(
                 -TIMESTEP * // this should use a variable to access the simulation timestep so we can readily change it from Python
                  (expk(-14.589996337890625k - 0.08599853515625k * membrane_voltage)
                 + expk(-1.8699951171875k + 0.070098876953125k * membrane_voltage)));

        // Update m
        additional_input->m_H = additional_input->m_inf_H +
                (additional_input->m_H - additional_input->m_inf_H) *
                additional_input->e_to_t_on_tau_m_H;

        // h (inactivation) is 1 and constant, so we will just ignore it.

        // Compute current
        additional_input->I_H =
                 - additional_input->g_H *
                additional_input->m_H *
                (membrane_voltage - additional_input->E_H);

        currents[0] = additional_input->I_H;
//------------------------------------------------------------------------
       // Calcium Current.

       // Update m
       additional_input->m_inf_T = 1k
       / (1k + expk(-(membrane_voltage+59k) * 0.161285400390625k)); //1/6.2=0.161290322

       additional_input->e_to_t_on_tau_m_T = expk(
          -TIMESTEP /
          (0.1300048828125k + 0.220001220703125k / (expk(-0.05987548828125k * (membrane_voltage+132k))             // 1/16.7=0.05988023952
                             + expk(0.054931640625k * (membrane_voltage + 16.79998779296875k)))));    // 1/18.2=0.05494505494

       additional_input->m_T = additional_input->m_inf_T +
               (additional_input->m_T - additional_input->m_inf_T) *
                additional_input->e_to_t_on_tau_m_T;

       // Update h
       additional_input->h_inf_T = 1k
    		   	   / (1k + expk((membrane_voltage + 83.0k)*0.25k)); //1/4=0.25

       additional_input->e_to_t_on_tau_h_T = expk(
           -TIMESTEP /
           (8.20001220703125k +
           (56.600006103515625k + 0.269989013671875k * expk((membrane_voltage + 115.20001220703125k) * 0.20001220703125k)) / // 1/5.0=0.2
           (1.0k + expk((membrane_voltage + 86.0k) * 0.3125k))));                  // 1/3.2=0.3125

       additional_input->h_T = additional_input->h_inf_T +
               (additional_input->h_T - additional_input->h_inf_T) *
                additional_input->e_to_t_on_tau_h_T;

       // Compute current
       additional_input->I_T =
                 - additional_input->g_T *
                additional_input->m_T *
                additional_input->m_T *
                additional_input->h_T *
               (membrane_voltage - additional_input->E_T);

       currents[1] = additional_input->I_T;

//--////-//------------------------------------------------------------------------
        // Sodium Current.
//        additional_input->g_NaP = 0.5k;

        additional_input->m_inf_NaP = 1k / (1k
                                  + expk(-MULT_ROUND_NEAREST_ACCUM(
			(membrane_voltage+55.70001220703125k),ulrbits(557787961)))); // 1/7.7 = 0.129870129

        // h (inactivation) is 1 and constant, so we will just ignore it.
        additional_input->I_NaP =
                 - MULT_ROUND_NEAREST_ACCUM(additional_input->g_NaP,
                 MULT_ROUND_NEAREST_ACCUM(additional_input->m_inf_NaP,
                 MULT_ROUND_NEAREST_ACCUM(additional_input->m_inf_NaP,
                 MULT_ROUND_NEAREST_ACCUM(additional_input->m_inf_NaP,
                (membrane_voltage - additional_input->E_NaP)))));

        currents[2] = additional_input->I_NaP;
//--////-//------------------------------------------------------------------------

        additional_input->D_influx = ulrbits(4294967) + MULT_ROUND_NEAREST_ACCUM(1250.0k, ulrbits(107374182))
        	/ (1.0k + expk(-MULT_ROUND_NEAREST_ACCUM((membrane_voltage - -10.0k), ulrbits(858993459)))); //1/5 = 0.2


        // Update D (Same form as LIF dV/dt solution)
        additional_input->D = additional_input->D_influx +
                              MULT_ROUND_NEAREST_ACCUM((additional_input->D
                              - additional_input->D_influx),
                              additional_input->e_to_t_on_tau_m_DK);

        accum D_cube = MULT_ROUND_NEAREST_ACCUM((additional_input->D),
        		MULT_ROUND_NEAREST_ACCUM((additional_input->D),
        		MULT_ROUND_NEAREST_ACCUM((additional_input->D),
				sqrtk(additional_input->D)))
//        		* (additional_input->D)
        		);
        additional_input->m_inf_DK = D_cube / (D_cube +
//        		0.015625k);   // 0.25^3 = 0.015625k
        		0.0078125k);  // 0.25^3.5 = 0.0078125
//        		0.00390625k); // 0.25^4 = 0.00390625k


        additional_input->I_DK = - MULT_ROUND_NEAREST_ACCUM(additional_input->g_DK,
                                 MULT_ROUND_NEAREST_ACCUM(additional_input->m_inf_DK,
                                 (membrane_voltage - additional_input->E_DK)));

        currents[0] = additional_input->D;
        currents[3] = additional_input->I_DK;

        //    _print_additional_input_params(additional_input);
//------------------------------------------------------------------------
//     profiler_write_entry_disable_irq_fiq(
//          PROFILER_EXIT | PROFILER_INTRINSIC_CURRENT);
//------------------------------------------------------------------------

     return   &currents[0];
//    		 additional_input->I_H +
//    		 additional_input->I_T +
//			 additional_input->I_NaP +
//			 additional_input->I_DK;
}

static void additional_input_has_spiked(
      additional_input_pointer_t additional_input) {
        // Do nothing.
	use(additional_input);
        }


#endif // _ADDITIONAL_INPUT_PACEMAKER_H_
