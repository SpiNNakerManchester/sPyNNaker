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

void error_function(REAL argument, mathsbox_t *restrict mathsbox){
/*
 *   Error function with integral computing by midpoint method
 *   Will do the Simpson if ITCM is ok
 *   
 *   Sampling of error function is maybe connected to the time_step need to investigate.
 */
    mathsbox->err_func = 0.;
    REAL step = argument/mathsbox->error_func_sample;
    REAL x;
    REAL t;
    //REAL Pi = 3.1415927;// here was a k
    REAL two_over_sqrt_Pi = REAL_CONST(1.128379167); //APPROXIMATION
    REAL Erf = ZERO;//mathsbox->err_func;
    REAL Erfc = ZERO;
    
    for(x=0; x<=argument; x+=step){
        //Erfc +=  factor*(2/sqrtk(Pi))*expk(-(t*t)); // the real one overflowed ITCM
        t = x + REAL_HALF(step);
        Erf +=  step*two_over_sqrt_Pi*expk(-(t*t)); //working like this one
    }
    Erfc = ONE-Erf;

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
    //REAL P4 = Pfit->P4;
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

    //REAL Fe, Fi;
    //REAL muGe, muGi, muG;
    //REAL Ue, Ui;
    //REAL Tm, Tv;
    
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

    REAL Fe = Ve * (REAL_CONST(1.)-gei)*pconnec*Ntot; // default is 1 !!
    REAL Fi = Vi * gei*pconnec*Ntot;
    
    /* normaly = Ve*Te*Qe*Ke with Ke = p*N_exc what it is?
        -> here N_exc = (1-gei)*Ntot*pconnec
        So give the same
    */
    REAL muGe = Qe*Te*Fe; //=Ve*Qe*Te*Ke
    REAL muGi = Qi*Ti*Fi;

    REAL muG = Gl + muGe + muGi;
    
    if (muG < ACS_DBL_TINY){
        muG += ACS_DBL_TINY;
    }

    pNetwork->muV = (muGe*Ee + muGi*Ei + Gl*El - W)/muG; //Thomas : maybe will add explicitely a and b?


    pNetwork->muGn = muG/Gl;

    REAL Tm = Cm/muG;

    REAL Ue = Qe*(Ee-pNetwork->muV)/muG;
    REAL Ui = Qi*(Ei-pNetwork->muV)/muG;
    

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
    
    REAL Tv = ( Fe*(Ue*Te)*(Ue*Te) + Fi*(Ti*Ui)*(Ti*Ui))\
        /(Fe*(Ue*Te)*(Ue*Te)/(Te+Tm) + Fi*(Ti*Ui)*(Ti*Ui)/(Ti+Tm));
    
    if (Tv < ACS_DBL_TINY){
        Tv += ACS_DBL_TINY;
    }
    /*
    pNetwork->TvN = Tv*Gl/Cm; // Thomas : Heu, useless no??
    */
    pNetwork->TvN = Tv;
    

}


void TF(REAL Ve, REAL Vi, REAL W,
        ParamsFromNetwork_t *restrict pNetwork,
        pFitPolynomial_t *restrict Pfit,
        mathsbox_t *restrict mathsbox){

/*
    State-variables are directly connected to the struct
    parameters are put in local in order to make the code clear.

*/
    
    
    
    
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

    
    /*
    normalement sqrt:
        argument = (pNetwork->Vthre - pNetwork->muV)/sqrtk(REAL_CONST(2.))/pNetwork->sV;

    */
    if (pNetwork->sV<ACS_DBL_TINY){
        pNetwork->sV += ACS_DBL_TINY;
    }
    //factor = REAL_HALF(Gl/(pNetwork->TvN * Cm));
    REAL argument = (pNetwork->Vthre - pNetwork->muV)/(REAL_CONST(1.4142137)*pNetwork->sV);

    error_function(argument, mathsbox);

    /*
    REAL Gl = pNetwork->Gl;
    REAL Cm = pNetwork->Cm;
    pNetwork->Fout_th = (HALF*Gl) * mathsbox->err_func / (Cm*pNetwork->TvN);// In fact = 1/(2.*Tv) * err_func , that's it'!!!
    If remove that's will do less instruction
    
    Put TvN<-:Tv because Tv not in pNetwork
    */
    pNetwork->Fout_th = (HALF*pNetwork->TvN) * mathsbox->err_func ;


    if (pNetwork->Fout_th < ACS_DBL_TINY){
        pNetwork->Fout_th += ACS_DBL_TINY;
    }
    
}


void RK2_midpoint_MF(REAL h, meanfield_t *meanfield,
                     ParamsFromNetwork_t *restrict pNetwork,
                     pFitPolynomial_t *restrict Pfit_exc,
                     pFitPolynomial_t *restrict Pfit_inh,
                     mathsbox_t *restrict mathsbox) {
    
    /* Propose for now a=0
    *
    */

    REAL lastVe = meanfield->Ve;
    REAL lastVi = meanfield->Vi;
    REAL lastW = meanfield->w;
    
    REAL tauw = meanfield->tauw;
    REAL T_inv = meanfield->Timescale_inv;
    REAL b = meanfield->b;

    /*
    if (h=0.){
        lastW = meanfield->Ve*tauw*b;
    }
    else{
        lastW = meanfield->w;
    }
    */
               
    
    TF(lastVe, lastVi, lastW, pNetwork, Pfit_exc, mathsbox);    
    REAL lastTF_exc = pNetwork->Fout_th;
    
    
    TF(lastVe, lastVi, lastW, pNetwork, Pfit_inh, mathsbox);
    REAL lastTF_inh = pNetwork->Fout_th;
    
/*
 *   EULER Explicite method
 *   It's very instable if for now h<0.2 for 20ms
 *   
 *   NEED to give also the error of the method here :
 *   0.5*h^2*u''(t_n) + o(h^2)
 */
    
    /*
    
    REAL k1_exc = (lastTF_exc - lastVe)*T_inv;
    meanfield->Ve += h * k1_exc ;
    
    REAL k1_inh = (lastTF_inh - lastVi)*T_inv;
    meanfield->Vi += h * k1_inh ;
    
    REAL k1_W = -lastW/tauw + meanfield->b * lastVe;
    meanfield->w += h * k1_W;
    
    */
    
/*
 *  RUNGE-KUTTA 2nd order Midpoint
 */
    
    
    //cut more the equation for underflowed ITCM!!
    REAL k1_exc = (lastTF_exc - lastVe)*T_inv;
    REAL alpha_exc = lastVe + h*k1_exc;
    REAL k2_exc = (lastTF_exc - alpha_exc )*T_inv;
    
    meanfield->Ve += REAL_HALF(h*(k1_exc + k2_exc));
        
    REAL k1_inh = (lastTF_inh - lastVi)*T_inv;
    REAL alpha_inh = lastVi + h*k1_inh;
    REAL k2_inh = (lastTF_inh - alpha_inh)*T_inv;
    
    meanfield->Vi += REAL_HALF(h*(k1_inh + k2_inh));
    
    REAL k1_W = -lastW/tauw + b * lastVe;
    REAL alpha_w = lastW + h*k1_W;
    REAL k2_W = -alpha_w/tauw + b * lastVe;
 
    meanfield->w += REAL_HALF(h*(k1_W+k2_W));


}

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
