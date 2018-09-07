#ifndef _ADDITIONAL_INPUT_ALL_CURRENTS_
#define _ADDITIONAL_INPUT_ALL_CURRENTS_

#include "additional_input.h"

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
    accum    D_infinity;  // instead of h_inf_DK
    // Voltage Clamp
    accum      v_clamp;    // voltage for voltage clamp [mV], hold voltage is just V_rest
    uint32_t  s_clamp;    // clamp starting time [timesteps]
    uint32_t  t_clamp;    // clamp duration [timesteps]
    //TODO:  maybe more efficient to get dt from other part of the software?
    accum    dt;
} additional_input_t;

// Variables to control 'patch clamp' tests
static input_t local_v;

// Variable to set m = m_inf on first timestep.
static uint32_t n_dt = 0;


static input_t additional_input_get_input_value_as_current(
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
//------------------------------------------------------------------------
    profiler_write_entry_disable_irq_fiq(
        PROFILER_ENTER | PROFILER_INTRINSIC_CURRENT);
//------------------------------------------------------------------------
        // Pacemaker Current.
        additional_input->g_H = 0.015k;

        additional_input->m_inf_H = 1k / (1k + expk((membrane_voltage+75k)/5.5k));

        // hardcode initial value for m as m_inf may cause an overhead on the profiling
        if (n_dt == 0){
            additional_input->m_H = additional_input->m_inf_H;
        }
//        n_dt += 1;

        additional_input->e_to_t_on_tau_m_H =
                  expk(
                 -1.0k *
                  (expk(-14.59k - 0.086k * membrane_voltage)
                 + expk(-1.87k + 0.0701k * membrane_voltage)));

        // Update m
        additional_input->m_H = additional_input->m_inf_H +
                (additional_input->m_H - additional_input->m_inf_H) *
                additional_input->e_to_t_on_tau_m_H;

        // h (inactivation) is 1 and constant, so we will just ignore it.
        additional_input->I_H =
                additional_input->g_H *
                additional_input->m_H *
                (membrane_voltage - additional_input->E_H);
//------------------------------------------------------------------------
       // Calcium Current.
       additional_input->g_T = 0.003k;

       additional_input->m_inf_T = 1k
       / (1k + expk(-(membrane_voltage+59k) * 0.16129k)); //1/6.2=0.161290322

       additional_input->h_inf_T = 1k
       / (1k + expk((membrane_voltage + 83.0k)*0.25k)); //1/4=0.25

       // hardcode initial value for m as m_inf and for h as h_inf
       if (n_dt == 0){
           additional_input->m_T = additional_input->m_inf_T;
           additional_input->h_T = additional_input->h_inf_T;
       }

       additional_input->e_to_t_on_tau_m_T = expk(
          -1.0k /
          (0.13k + 0.22k / (expk(-0.05988k * (membrane_voltage+132k))             // 1/16.7=0.05988023952
                             + expk(0.054945k * (membrane_voltage + 16.8k)))));    // 1/18.2=0.05494505494

       additional_input->e_to_t_on_tau_h_T = expk(
           -1.0k /
           (8.2k +
           (56.6k + 0.27k * expk((membrane_voltage + 115.2k) * 0.2k)) /            // 1/5.0=0.2
           (1.0k + expk((membrane_voltage + 86.0k) * 0.3125k))));                  // 1/3.2=0.3125

       // Update m
       additional_input->m_T = additional_input->m_inf_T +
               (additional_input->m_T - additional_input->m_inf_T) *
                additional_input->e_to_t_on_tau_m_T;

       // Update h
       additional_input->h_T = additional_input->h_inf_T +
               (additional_input->h_T - additional_input->h_inf_T) *
                additional_input->e_to_t_on_tau_h_T;

       additional_input->I_T =
                additional_input->g_T *
                additional_input->m_T *
                additional_input->m_T *
                additional_input->h_T *
               (membrane_voltage - additional_input->E_T);

//--////-//------------------------------------------------------------------------
        // Sodium Current.
        additional_input->g_NaP = 0.007k;

        additional_input->m_inf_NaP = 1k / (1k
                                  + expk(-(membrane_voltage+55.7k)*0.12987k)); // 1/7.7 = 0.129870129

        // h (inactivation) is 1 and constant, so we will just ignore it.
        additional_input->I_NaP =
                 additional_input->g_NaP *
                 additional_input->m_inf_NaP *
                 additional_input->m_inf_NaP *
                 additional_input->m_inf_NaP *
                (membrane_voltage - additional_input->E_NaP);

//--////-//------------------------------------------------------------------------

        additional_input->g_DK = 1.25k;

        additional_input->e_to_t_on_tau_m_DK = 0.367879k; // exp(-0.1/1250)

        additional_input->D_infinity = 0.001k + 1250.0k *0.025k
                                       / (1.0k + expk(-(membrane_voltage - -10.0k) * 0.2k)); //1/5 = 0.2

        // hardcode initial value for D as D_infinity
        if (n_dt == 0){
        additional_input->D = additional_input->D_infinity;
        }
        n_dt += 1;

        // Update D (Same form as LIF dV/dt solution)
        additional_input->D = additional_input->D_infinity +
                              (additional_input->D
                             - additional_input->D_infinity)
                             * additional_input->e_to_t_on_tau_m_DK;

        accum D_cube = (additional_input->D-0.05) * (additional_input->D-0.05) *  (additional_input->D-0.05);
         // the 0.05 factor above was added to compensate the difference from 3.5 to 3.0 exponent, in this way
         // the error is minimal. BUTVERIFY IF THIS IS STILL NEEDED.

        additional_input->m_inf_DK = 1k / (1k + (0.0078125k /  // 0.25^3.5 = 0.0078125
                                  (0.00001+ D_cube  // the 0.00001 factor was added to avoid divergence of the type 1/0.
                                  )));              // TODO: Actual exponent is D^3.5.

        additional_input->I_DK = - additional_input->g_DK
                                 * additional_input->m_inf_DK
                                 * (membrane_voltage - additional_input->E_DK);

        //    _print_additional_input_params(additional_input);
//------------------------------------------------------------------------
     profiler_write_entry_disable_irq_fiq(
          PROFILER_EXIT | PROFILER_INTRINSIC_CURRENT);
//------------------------------------------------------------------------

     return additional_input->I_H + additional_input->I_T + additional_input->I_NaP + additional_input->I_DK;
}

static void additional_input_has_spiked(
      additional_input_pointer_t additional_input) {
        // Do nothing.
        }

static inline void _print_additional_input_params(additional_input_t* additional_input){

                 log_debug("Pacemaker Current \n"
                       " I_H: %k, g_H: %k, E_H: %k,   \n"
                       " m_H: %k,m_inf_H: %k,e_to_t_on_tau_m_H: %k, \n"
                       " Calcium Current: \n"
                       "I_T: %k, g_T: %k, E_T: %k,\n"
                       "m_T: %k,m_inf_T: %k, e_to_t_on_tau_m_T: %k,\n"
                       "h_T: %k, h_inf_T: %k, e_to_t_on_tau_h_T: %k,\n"
                       " Sodium Current:  \n"
                       "I_NaP: %k, g_NaP: %k,E_NaP: %k,\n"
                       "m_inf_NaP: %k,\n"
                       " Potassium Current:   \n"
                       "I_DK: %k, g_DK: %k, E_DK: %k, \n"
                       " m_inf_DK: %k,e_to_t_on_tau_m_DK: %k,\n"
                       " D: %k, D_infinity: %k,\n"
                       " Voltage Clamp:      \n"
                       " v_clamp: %k, s_clamp: %k, t_clamp: %k, dt: %k",
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
                       additional_input->D_infinity,
                       // Voltage Clamp
                       additional_input->v_clamp,
                       additional_input->s_clamp,
                       additional_input->t_clamp,
                       additional_input->dt);
}

#endif // _ADDITIONAL_INPUT_PACEMAKER_H_
