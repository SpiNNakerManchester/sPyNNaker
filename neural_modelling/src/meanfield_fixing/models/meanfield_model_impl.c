/*
 * Copyright (c) 2017-2019 The University of Manchester
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

//! \file
//! \brief Izhekevich neuron implementation
#include "meanfield_model_impl.h"
#include "mathsbox.h"
#include "config.h"

#include <debug.h>

//! The global parameters of the Izhekevich neuron model
static const global_neuron_params_t *global_params;

/*! \brief For linear membrane voltages, 1.5 is the correct value. However
 * with actual membrane voltage behaviour and tested over an wide range of
 * use cases 1.85 gives slightly better spike timings.
 */
//static const REAL SIMPLE_TQ_OFFSET = REAL_CONST(1.85);
/*
/////////////////////////////////////////////////////////////
#if 0
// definition for Izhikevich neuron
static inline void neuron_ode(
        REAL t, REAL stateVar[], REAL dstateVar_dt[],
        neuron_t *neuron, REAL input_this_timestep) {
    REAL V_now = stateVar[1];
    REAL U_now = stateVar[2];
    log_debug(" sv1 %9.4k  V %9.4k --- sv2 %9.4k  U %9.4k\n", stateVar[1],
            neuron->V, stateVar[2], neuron->U);

    // Update V
    dstateVar_dt[1] =
            REAL_CONST(140.0)
            + (REAL_CONST(5.0) + REAL_CONST(0.0400) * V_now) * V_now - U_now
            + input_this_timestep;

    // Update U
    dstateVar_dt[2] = neuron->A * (neuron->B * V_now - U_now);
}
#endif
*/

//! \brief The original model uses 0.04, but this (1 ULP larger?) gives better
//! numeric stability.
//!
//! Thanks to Mantas Mikaitis for this!
//static const REAL MAGIC_MULTIPLIER = REAL_CONST(0.040008544921875);


/* ####################################################################
    reuse of izk for meanfields
    ###################################################################
    */

void error_function( REAL x, REAL factor, mathsbox_t *restrict mathsbox){ 
//devra coder fonction powerof 

    REAL dt = x/mathsbox->error_func_sample;
    REAL t;
    REAL Pi = 3.1415927;
    REAL Erfc = mathsbox->err_func;
    for(t=0; t==x; t+=dt){
        //Erfc += dt; //test otherwise IDTM overload
        //Erfc +=  factor*(2/sqrtk(Pi))*expk(-(t*t)); // the real one
        Erfc += factor+t*t;//fake one
    }
    
    mathsbox->err_func = Erfc;
    
    //return Erfc;

}


void threshold_func(config_t *restrict config)
{
    /*
    setting by default to True the square
    because when use by external modules, coeff[5:]=np.zeros(3)
    in the case of a linear threshold
    */
    /*NEED TO AVOID DIVISION AS POSSIBLE
        but not for now     
    */
    /*
    config->muV0=-0.06;
    config->DmuV0=0.01;
    
    config->sV0=0.004;
    config->DsV0=0.006;
    
    config->TvN0=0.5;
    config->DTvN0=1.;
    
    config->muV=0.;
    config->sV=0.;
    config->muGn=0.;
    config->TvN=0.;
    config->Vthre=0.;
    config->Fout_th=0.;
    */
    
    //        + 0.\ //P4*np.log(muGn)
    /*
    config->Vthre = config->P0\
        + config->P1*(config->muV-config->muV0)/config->DmuV0\
        + config->P2*(config->sV-config->sV0)/config->DsV0\
        + config->P3*(config->TvN-config->TvN0)/config->DTvN0\
        + config->P5*((config->muV-config->muV0)/config->DmuV0)*((config->muV-config->muV0)/config->DmuV0)\
        + config->P6*((config->sV-config->sV0)/config->DsV0)*((config->sV-config->sV0)/config->DsV0)\
        + config->P7*((config->TvN-config->TvN0)/config->DTvN0)*((config->TvN-config->TvN0)/config->DTvN0)\
        + config->P8*(config->muV-config->muV0)/config->DmuV0*(config->sV-config->sV0)/config->DsV0\
        + config->P9*(config->muV-config->muV0)/config->DmuV0*(config->TvN-config->TvN0)/config->DTvN0\
        + config->P10*(config->sV-config->sV0)/config->DsV0*(config->TvN-config->TvN0)/config->DTvN0;
        */
    
    config->Vthre = config->P0;
        
    //return config->Vthre;
    
    }

/*
    REAL ONE get_fluct_regime_varsup
*/
/*
void get_fluct_regime_varsup(REAL Ve, REAL Vi, config_t *restrict params)
{
    //takes 880 bytes overflowed ITCM 
    
    REAL Fe;
    REAL Fi;
    REAL muGe, muGi, muG;
    REAL Ue, Ui;
    REAL Tm, Tv;
    

    // here TOTAL (sum over synapses) excitatory and inhibitory input

    Fe = Ve * (1.-params->gei)*params->pconnec*params->Ntot; // default is 1 !!
    Fi = Vi * params->gei*params->pconnec*params->Ntot;

    muGe = params->Qe*params->Te*Ve;
    muGi = params->Qi*params->Ti*Vi;

    muG = params->Gl+muGe+muGi;

    params->muV = (muGe*params->Ee+muGi*params->Ei+params->Gl*params->El)/muG;
    

    params->muGn = muG/params->Gl;
    
    Tm = params->Cm/muG;

    Ue = params->Qe/muG*(params->Ee-params->muV);
    Ui = params->Qi/muG*(params->Ei-params->muV);

    
   //PENSEZ a enlever autant de division que possible

    params->sV = sqrtk(Fe*(Ue*params->Te)*(Ue*params->Te)/2./(params->Te+Tm)+\
                 Fi*(params->Ti*Ui)*(params->Ti*Ui)/2./(params->Ti+Tm));
    
    if (params->sV < 1e-8){
        params->sV = 1e-8;
    }

    if (Fe<1e-9)//just to insure a non zero division,
    {
        Fe += 1e-9;
    }
    else if (Fi<1e-9)
    {
        Fi += 1e-9;
    }

    Tv = ( Fe*(Ue*params->Te)*(Ue*params->Te) + Fi*(params->Ti*Ui)*(params->Ti*Ui))\
        /(Fe*(Ue*params->Te)*(Ue*params->Te)/(params->Te+Tm)\
          + Fi*(params->Ti*Ui)*(params->Ti*Ui)/(params->Ti+Tm));
    
    params->TvN = Tv*params->Gl/params->Cm;

    //return params->muV;//, sV+1e-12, muGn, TvN
}
*/


// FAKE ONE get_fluct_regime_varsup
//where all division are removed

void get_fluct_regime_varsup(REAL Ve, REAL Vi, config_t *restrict params)
{
    //takes 880 bytes overflowed ITCM 
    
    REAL Fe;
    REAL Fi;
    REAL muGe, muGi, muG;
    REAL Ue, Ui;
    REAL Tm, Tv;
    

    // here TOTAL (sum over synapses) excitatory and inhibitory input

    Fe = Ve * (1.-params->gei)*params->pconnec*params->Ntot; // default is 1 !!
    Fi = Vi * params->gei*params->pconnec*params->Ntot;

    muGe = params->Qe*params->Te*Ve;
    muGi = params->Qi*params->Ti*Vi;

    muG = params->Gl+muGe+muGi;

    params->muV = (muGe*params->Ee+muGi*params->Ei+params->Gl*params->El); //fake one

    params->muGn = muG; //fake one
    
    Tm = params->Cm/muG; //fake one

    Ue = params->Qe; //fake one
    Ui = params->Qi; //fake one

    
   //PENSEZ a enlever autant de division que possible

    params->sV = Fe*(Ue*params->Te)*(Ue*params->Te)+\
                 Fi*(params->Ti*Ui)*(params->Ti*Ui);// fake one

    if (params->sV < 1e-8){
        params->sV = 1e-8;
    }

    if (Fe<1e-9)//just to insure a non zero division,
    {
        Fe += 1e-9;
    }
    else if (Fi<1e-9)
    {
        Fi += 1e-9;
    }

    Tv = ( Fe*(Ue*params->Te)*(Ue*params->Te) +\
          Fi*(params->Ti*Ui)*(params->Ti*Ui)); //fake one    

    params->TvN = Tv*params->Gl; //fake one
    

    //return params->muV;//, sV+1e-12, muGn, TvN
}

//END of the get_fluct_regime_varsup FAKE



void TF(REAL Ve, REAL Vi, meanfield_t *meanfield, config_t *restrict config, mathsbox_t *restrict mathsbox){
    
// argument are fe, fi and pseq_params
//   problem is to implement it with params and instruction coming from
//   DTCM and ITCM.
//   when get_fluct_regime_varsup is ON  takes 1360 bytes overflowed ITCM 
   

    REAL limit;
    REAL argument;
    
    if (Ve < REAL_CONST(1e-8)){
        Ve = REAL_CONST(1e-8);
    }
    if (Vi < REAL_CONST(1e-8)){
        Vi = REAL_CONST(1e-8);
    }
    
    get_fluct_regime_varsup(Ve, Vi, config);
    threshold_func(config);

    if (config->sV<REAL_CONST(1e-4)){
        config->sV = REAL_CONST(1e-4);
    }

    limit = 10;//REAL_HALF(config->Gl/(config->TvN * config->Cm));
    argument = config->Vthre;//(config->Vthre - config->muV)/sqrtk(REAL_CONST(2.))/config->sV;
    
//    config->Fout_th = error_function(factor, argument, mathsbox);
    error_function(limit, argument, mathsbox);


    if (config->Fout_th < REAL_CONST(1e-8)){
        config->Fout_th = REAL_CONST(1e-8);
    }
    
    //return config->Fout_th;
}


void RK2_midpoint_MF(REAL h, meanfield_t *meanfield, config_t *restrict config, mathsbox_t *restrict mathsbox) {
/* need to input T_inv time scale where the 1/T will be done (and rounding)
on the user computer before send it to the DTCM.
*/
    REAL lastVe = meanfield->Ve;
    REAL T_inv = meanfield->Timescale_inv;
    //TF(lastVe,1.,meanfield, config, mathsbox);
    REAL lastTF = 1.0; //config->Fout_th;
    
    
    //configVe stand for TF1 i.e TF for exitatory pop. SO configVi is for TF2
    //In fact no configVe and configVi just config, all in the same file.
    

    /*meanfield->Ve += lastVe\
        + REAL_HALF(TF(lastVe,1,meanfield, config, mathsbox) - lastVe)\
        *(REAL_CONST(2.0)-h)*h;
        */
    
    meanfield->Ve += lastVe\
        + REAL_HALF(lastTF - lastVe)\
        *(REAL_CONST(2.0)-h)*h;
    meanfield->Ve =  meanfield->Ve * T_inv;
}

        
/*##############################################################################
end of reuse
#################################################################################
*/

/*!
 * \brief Midpoint is best balance between speed and accuracy so far.
 * \details From ODE solver comparison work, paper shows that Trapezoid version
 *      gives better accuracy at small speed cost
 * \param[in] h: threshold
 * \param[in,out] neuron: The model being updated
 * \param[in] input_this_timestep: the input
 */
/*static inline void rk2_kernel_midpoint(
        REAL h, neuron_t *neuron, REAL input_this_timestep) {
    // to match Mathematica names
    REAL lastV1 = neuron->V;
    REAL lastU1 = neuron->U;
    REAL a = neuron->A;
    REAL b = neuron->B;

    REAL pre_alph = REAL_CONST(140.0) + input_this_timestep - lastU1;
    REAL alpha = pre_alph
            + (REAL_CONST(5.0) + MAGIC_MULTIPLIER * lastV1) * lastV1;
    REAL eta = lastV1 + REAL_HALF(h * alpha);

    // could be represented as a long fract?
    REAL beta = REAL_HALF(h * (b * lastV1 - lastU1) * a);

    neuron->V += h * (pre_alph - beta
            + (REAL_CONST(5.0) + MAGIC_MULTIPLIER * eta) * eta);

    neuron->U += a * h * (-lastU1 - beta + b * eta);
}
*/


void meanfield_model_set_global_neuron_params(
        const global_neuron_params_t *params) {
    global_params = params;
}

/*perhaps when we will do more than one MF we could uses "num_excitatory_inputs" like the number of ex MF and in MF?
  and maybe is there some contamanation from the neightbourest neighbour MF!
*/
state_t meanfield_model_state_update(
        meanfield_t *restrict meanfield, config_t *restrict config, mathsbox_t *restrict mathsbox){
    /*
        uint16_t num_excitatory_inputs, const input_t *exc_input,
		uint16_t num_inhibitory_inputs, const input_t *inh_input,
		input_t external_bias, meanfield_t *restrict meanfield,
        config_t *restrict config) {
    REAL total_exc = 0;
    REAL total_inh = 0;

    for (int i =0; i<num_excitatory_inputs; i++) {
        total_exc += exc_input[i];
    }
    for (int i =0; i<num_inhibitory_inputs; i++) {
        total_inh += inh_input[i];
    }

    //input_t input_this_timestep = total_exc - total_inh
    //        + external_bias + neuron->I_offset;
    */

    // the best AR update so far
    RK2_midpoint_MF(meanfield->this_h, meanfield, config, mathsbox);
    meanfield->this_h = global_params->machine_timestep_ms;

    return meanfield->Ve;
}



void neuron_model_has_spiked(meanfield_t *restrict meanfield) {
    log_debug("in neuron_model_has_spiked, time is ",
              global_params->machine_timestep_ms);
    // reset membrane voltage
    //neuron->V = neuron->C;

    // offset 2nd state variable
    //neuron->U += neuron->D;

    // simple threshold correction - next timestep (only) gets a bump
    //neuron->this_h = global_params->machine_timestep_ms * SIMPLE_TQ_OFFSET;
}

//change name neuron -> meanfield and membrane -> rate
state_t meanfield_model_get_firing_rate(const meanfield_t *meanfield) {
    return meanfield->Ve;
}

void meanfield_model_print_state_variables(const meanfield_t *meanfield) {
    log_debug("Ve = %11.4k ", meanfield->Ve);
    //log_debug("U = %11.4k ", meanfield->Vi);
}

void meanfield_model_print_parameters(const meanfield_t *meanfield) {
    log_debug("Ve = %11.4k ", meanfield->Ve);
    //log_debug("Vi = %11.4k ", meanfield->Vi);
    //log_debug("B = %11.4k ", neuron->B);
    //log_debug("C = %11.4k ", neuron->C);
    //log_debug("D = %11.4k ", neuron->D);

    //log_debug("I = %11.4k \n", neuron->I_offset);
}
