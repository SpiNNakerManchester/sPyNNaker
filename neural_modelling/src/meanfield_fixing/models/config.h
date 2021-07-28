#ifndef _CONFIG_H_
#define _CONFIG_H_

#include "meanfield_model.h"


/*struct config_t;
typedef struct config_t config_t;
typedef struct config_t* config_t;*/

typedef struct config_t {
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

    REAL P0;
    REAL P1;
    REAL P2;
    REAL P3;
    REAL P4;
    REAL P5;
    REAL P6;
    REAL P7;
    REAL P8;
    REAL P9;
    REAL P10;
    
    // Variable-state parameters
    //REAL fe;
    //REAL fi;
    
    REAL muV;//:=0.0;
    REAL muV0;
    //muV0 = -60e-3;
    REAL DmuV0;// = 10e-3;
    
    REAL sV;//=0.0;
    REAL sV0;// = 4e-3;
    REAL DsV0;// = 6e-3;
        
    REAL muGn;//=0.0;
    
    REAL TvN;//=0.0;
    REAL TvN0;// = 0.5;
    REAL DTvN0;// = 1.;
    
    REAL Vthre;//=0.0;
    
    REAL Fout_th;//=0.0;
} config_t;

/*
typedef struct global_toolbox_params_t {
    REAL this_h;
    REAL this_time;
} global_toolbox_params_t;
*/


#endif