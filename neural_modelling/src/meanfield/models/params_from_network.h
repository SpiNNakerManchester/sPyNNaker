#ifndef _PARAMS_FROM_NETWORK_H_
#define _PARAMS_FROM_NETWORK_H_

#include "../../meanfield/models/meanfield_model.h"


/*struct config_t;
typedef struct config_t config_t;
typedef struct config_t* config_t;*/

typedef struct ParamsFromNetwork_t {
    // nominally 'fixed' parameters
    REAL pconnec;
    REAL Qe;
    REAL Qi;
    REAL Te;
    REAL Ti;
    REAL Ee;
    REAL Ei;
    REAL Ntot;
    REAL gei;
    REAL ext_drive;
    REAL afferent_exc_fraction;
    
    REAL Gl;
    REAL Cm;
    REAL El;
    
    // Variable-state parameters
    //REAL fe;
    //REAL fi;
    
    REAL muV;
    REAL muV0;
    
    REAL DmuV0;
    
    REAL sV;
    REAL sV0;
    REAL DsV0;
        
    REAL muGn;
    
    REAL TvN;
    REAL TvN0;
    REAL DTvN0;
    
    REAL Vthre;
    
    REAL Fout_th;
} ParamsFromNetwork_t;

/*
typedef struct global_toolbox_params_t {
    REAL this_h;
    REAL this_time;
} global_toolbox_params_t;
*/


#endif