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
#include "../../meanfield/models/meanfield_model_impl.h"

#include <debug.h>
#include "../../meanfield/models/params_from_network.h"
#include "../../meanfield/models/mathsbox.h"
#include "../../meanfield/models/P_fit_polynomial.h"
//#include "../../common/maths-util.h" // i.o to use SQRT(x) and SQR(a)

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

void error_function( REAL x, REAL argument, mathsbox_t *restrict mathsbox){
//devra coder fonction powerof

    REAL dt = x/mathsbox->error_func_sample;
    REAL t;
    //REAL Pi = 3.1415927;// here was a k
    REAL two_over_sqrt_Pi = REAL_CONST(1.128379167); //APPROXIMATION
    REAL Erfc = 0.;//mathsbox->err_func;
    for(t=0; t<=x; t+=dt){
        //Erfc +=  factor*(2/sqrtk(Pi))*expk(-(t*t)); // the real one overflowed ITCM
        Erfc +=  argument*two_over_sqrt_Pi*expk(-(t*t)); //working like this one
    }

    mathsbox->err_func = Erfc;

}


void threshold_func(ParamsFromNetwork_t *restrict pNetwork, pFitPolynomial_t *restrict Pfit)
{
    /*
        threshold function coming from :
        Neural Computation 31, 653–680 (2019) doi:10.1162/neco_a_01173
        where P's are polynomials parameters involve in a 
        voltage-effective threshold.
    */
    /*
    setting by default to True the square
    because when use by external modules, coeff[5:]=np.zeros(3)
    in the case of a linear threshold
    */
    /*NEED TO AVOID DIVISION AS POSSIBLE
        but not for now
    */
   
    REAL muV0 = pNetwork->muV0;
    REAL DmuV0 = pNetwork->DmuV0;

    REAL sV0 = pNetwork->sV0;
    REAL DsV0 = pNetwork->DsV0;

    REAL TvN0 = pNetwork->TvN0;
    REAL DTvN0 = pNetwork->DTvN0;

    REAL muV = pNetwork->muV;
    REAL sV = pNetwork->sV;
    //REAL muGn = pNetwork->muGn;
    REAL TvN = pNetwork->TvN;
    REAL Vthre = pNetwork->Vthre;
    //REAL Fout_th = pNetwork->Fout_th;
    
    REAL P0 = Pfit->P0;
    REAL P1 = Pfit->P1;
    REAL P2 = Pfit->P2;
    REAL P3 = Pfit->P3;
    REAL P4 = Pfit->P4;
    REAL P5 = Pfit->P5;
    REAL P6 = Pfit->P6;
    REAL P7 = Pfit->P7;
    REAL P8 = Pfit->P8;
    REAL P9 = Pfit->P9;
    REAL P10 = Pfit->P10;

    //        + 0.\ //P4*np.log(muGn)
    
    Vthre = P0\
        + P1*(muV-muV0)/DmuV0\
        + P2*(sV-sV0)/DsV0\
        + P3*(TvN-TvN0)/DTvN0\
        + P5*((muV-muV0)/DmuV0)*((muV-muV0)/DmuV0)\
        + P6*((sV-sV0)/DsV0)*((sV-sV0)/DsV0)\
        + P7*((TvN-TvN0)/DTvN0)*((TvN-TvN0)/DTvN0)\
        + P8*((muV-muV0)/DmuV0)*((sV-sV0)/DsV0)\
        + P9*((muV-muV0)/DmuV0)*((TvN-TvN0)/DTvN0)\
        + P10*((sV-sV0)/DsV0)*((TvN-TvN0)/DTvN0);

    pNetwork->Vthre = Vthre;

    }

void get_fluct_regime_varsup(REAL Ve, REAL Vi, REAL W, ParamsFromNetwork_t *restrict pNetwork)
{

    REAL Fe;
    REAL Fi;
    REAL muGe, muGi, muG;
    REAL Ue, Ui;
    REAL Tm, Tv;
    
    REAL gei = pNetwork->gei;
    REAL pconnec = pNetwork->pconnec;
    REAL Ntot = pNetwork->Ntot;
    REAL Qe = pNetwork->Qe;
    REAL Qi = pNetwork->Qi;
    REAL Te = pNetwork->Te;
    REAL Ti = pNetwork->Ti;
    REAL Gl = pNetwork->Gl;
    REAL El = pNetwork->El;
    REAL Ei = pNetwork->Ei;
    REAL Ee = pNetwork->Ee;
    REAL Cm = pNetwork->Cm;
    
    
    
    //REAL muV = pNetwork->muV;
    //REAL muGn = pNetwork->muGn;
    //REAL sV = pNetwork->sV;
    //REAL TvN = pNetwork->TvN;
    
    // here TOTAL (sum over synapses) excitatory and inhibitory input

    Fe = Ve * (REAL_CONST(1.)-gei)*pconnec*Ntot; // default is 1 !!
    Fi = Vi * gei*pconnec*Ntot;
    
    muGe = Qe*Te*Ve; // normaly = Ve*Te*Qe*Ke with Ke = p*Nue what it is?
    muGi = Qi*Ti*Vi;

    muG = Gl+muGe+muGi;
    
    if (muG < ACS_DBL_TINY){
        muG += ACS_DBL_TINY;
    }

    pNetwork->muV = (muGe*Ee + muGi*Ei + Gl*El - W)/muG;


    pNetwork->muGn = muG/Gl;

    Tm = Cm/muG;

    Ue = Qe/muG*(Ee-pNetwork->muV);
    Ui = Qi/muG*(Ei-pNetwork->muV);


   /*
   normalement sqrt((Fe*(Ue*params->Te)*(Ue*params->Te)/2./(params->Te+Tm)+\
                 Fi*(params->Ti*Ui)*(params->Ti*Ui)/2./(params->Ti+Tm)))
   
   doit trouver une bonne fonction pour faire sqrt ...
   |->sqrtk() ne fonctionne pas !!!
    */
                 
    
    pNetwork->sV = Fe*(Ue*Te)*(Ue*Te)/REAL_CONST(2.)/(Te+Tm)\
               + Fi*(Ti*Ui)*(Ti*Ui)/REAL_CONST(2.)/(Ti+Tm);
    
    
    
    if (Fe<ACS_DBL_TINY)//just to insure a non zero division,
    {
        Fe += ACS_DBL_TINY;
    }
    else if (Fi<ACS_DBL_TINY)
    {
        Fi += ACS_DBL_TINY;
    }
    
    Tv = ( Fe*(Ue*Te)*(Ue*Te) + Fi*(Ti*Ui)*(Ti*Ui))\
        /(Fe*(Ue*Te)*(Ue*Te)/(Te+Tm) + Fi*(Ti*Ui)*(Ti*Ui)/(Ti+Tm));
    
    if (Tv < ACS_DBL_TINY){
        Tv += ACS_DBL_TINY;
    }    

    pNetwork->TvN = Tv*Gl/Cm;
    

}


void TF(REAL Ve, REAL Vi, REAL W,
        meanfield_t *meanfield,
        ParamsFromNetwork_t *restrict pNetwork,
        pFitPolynomial_t *restrict Pfit,
        mathsbox_t *restrict mathsbox){

/*
    State-variables are directly connected to the struct
    parameters are put in local in order to make the code clear.

*/


    REAL limit;
    REAL argument;
    
    REAL Gl = pNetwork->Gl;
    REAL Cm = pNetwork->Cm;
    
    
    if (pNetwork->Fout_th != ZERO){
        pNetwork->Fout_th = ACS_DBL_TINY;
    }

    if (Ve < ACS_DBL_TINY){
        Ve += ACS_DBL_TINY;
    }
    if (Vi < ACS_DBL_TINY){
        Vi += ACS_DBL_TINY;
    }

    get_fluct_regime_varsup(Ve, Vi, W, pNetwork);
    threshold_func(pNetwork, Pfit);

    limit = REAL_HALF(Gl/(pNetwork->TvN * Cm));
    /*
    normalement sqrt:
        argument = (pNetwork->Vthre - pNetwork->muV)/sqrtk(REAL_CONST(2.))/pNetwork->sV;

    */
    if (pNetwork->sV<ACS_DBL_TINY){
        pNetwork->sV += ACS_DBL_TINY;
    }
    argument = (pNetwork->Vthre - pNetwork->muV)/(REAL_CONST(1.4142137)*pNetwork->sV);

    error_function(limit, argument, mathsbox);
    /*
    if (pNetwork->P0 == 0.){
        mathsbox->err_func = 1; a simple test
    }
    */
    
    pNetwork->Fout_th = (HALF*Gl) * mathsbox->err_func / (Cm*pNetwork->TvN);// REAL ONE
    //pNetwork->Fout_th = mathsbox->err_func ; //TEST


    if (pNetwork->Fout_th < ACS_DBL_TINY){
        pNetwork->Fout_th += ACS_DBL_TINY;
    }
    
}


void RK2_midpoint_MF(REAL h, meanfield_t *meanfield,
                     ParamsFromNetwork_t *restrict pNetwork,
                     pFitPolynomial_t *restrict Pfit_exc,
                     pFitPolynomial_t *restrict Pfit_inh,
                     mathsbox_t *restrict mathsbox) {

    REAL lastVe = meanfield->Ve;
    REAL lastVi = meanfield->Vi;
    REAL lastW = meanfield->w;
    REAL tauw = meanfield->tauw;
    
    //REAL W_tauw;
       
    REAL T_inv = meanfield->Timescale_inv;
    
    TF(lastVe, lastVi, lastW, meanfield, pNetwork, Pfit_exc, mathsbox);    
    REAL lastTF_exc = pNetwork->Fout_th;
    
    
    TF(lastVe, lastVi, lastW, meanfield, pNetwork, Pfit_inh, mathsbox);
    REAL lastTF_inh = pNetwork->Fout_th;
    
    //configVe stand for TF1 i.e TF for exitatory pop. SO configVi is for TF2
    //In fact no configVe and configVi just config, all in the same file.
    /*
        some troubles maybe come from constants :
        from spynnaker.pyNN.utilities.constants 
        
        and
        
        pyNN/models/recorder.py
        
    */

    //cut more the equation for underflowed ITCM!!
    REAL k1_exc = (lastTF_exc - lastVe)*T_inv;
    REAL k2_exc = (lastTF_exc - (lastVe + h*k1_exc))*T_inv;
    
    meanfield->Ve += lastVe + REAL_HALF(h*(k1_exc + k2_exc));
    
    //meanfield->Ve += lastVe + (REAL_HALF(lastTF_exc - lastVe) * (REAL_CONST(2.0)-h) * h);
    //meanfield->Ve =  meanfield->Ve * T_inv;
    
    REAL k1_inh = (lastTF_inh - lastVi)*T_inv;
    REAL k2_inh = lastVi - h*k1_inh;//(lastTF_inh - (lastVi + h*k1_inh))*T_inv;
    
    meanfield->Vi += lastVi + REAL_HALF(h*(k1_inh + k2_inh));
    //meanfield->Vi += lastVi + (REAL_HALF(lastTF_inh - lastVi) * (REAL_CONST(2.0)-h) * h);
    //meanfield->Vi =  meanfield->Vi * ONE; //*T_inv normaly
    
    REAL k1_W = -lastW/tauw + meanfield->b * lastVe;
    REAL k2_W = lastW + h * k1_W;//-(lastW + h*k1_W)/tauw + meanfield->b * lastVe;
    
    //W_tauw = -lastW + meanfield->b*lastVe*tauw 
    //                 + meanfield->a*(pNetwork->muV-pNetwork->El)*tauw;
    //meanfield->w += meanfield->tauw ;
    meanfield->w += lastVi;//lastW ;//+ REAL_HALF(h*(k1_W+k2_W));
        
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
    meanfield_t *restrict meanfield,
    ParamsFromNetwork_t *restrict pNetwork,
    pFitPolynomial_t *restrict Pfit_exc,
    pFitPolynomial_t *restrict Pfit_inh,
    mathsbox_t *restrict mathsbox){
    /*
        uint16_t num_excitatory_inputs, const input_t *exc_input,
		uint16_t num_inhibitory_inputs, const input_t *inh_input,
		input_t external_bias, meanfield_t *restrict meanfield,
        ParamsFromNetwork_t *restrict pNetwork) {
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
    RK2_midpoint_MF(meanfield->this_h,
                    meanfield,
                    pNetwork,
                    Pfit_exc,
                    Pfit_inh,
                    mathsbox);
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
state_t meanfield_model_get_firing_rate_Ve(const meanfield_t *meanfield) {
    return meanfield->Ve;
}

state_t meanfield_model_get_firing_rate_Vi(const meanfield_t *meanfield) {
    return meanfield->Vi;
}

state_t meanfield_model_get_adaptation_W(const meanfield_t *meanfield){
    return meanfield->w;
}


void meanfield_model_print_state_variables(const meanfield_t *meanfield) {
    log_debug("Ve = %11.4k ", meanfield->Ve);
    log_debug("Vi = %11.4k ", meanfield->Vi);
    log_debug("W = %11.4k ", meanfield->w);
}

void meanfield_model_print_parameters(const meanfield_t *meanfield) {
    //log_debug("Ve = %11.4k ", meanfield->Ve);
    //log_debug("Vi = %11.4k ", meanfield->Vi);
    //log_debug("B = %11.4k ", neuron->B);
    //log_debug("C = %11.4k ", neuron->C);
    //log_debug("D = %11.4k ", neuron->D);

    //log_debug("I = %11.4k \n", neuron->I_offset);
}
