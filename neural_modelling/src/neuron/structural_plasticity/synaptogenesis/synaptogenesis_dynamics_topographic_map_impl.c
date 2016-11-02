#include "../synaptogenesis_dynamics.h"
#include <debug.h>


//---------------------------------------
// Structures
//---------------------------------------
typedef struct {
    uint32_t no_vertices;
    uint32_t* key_atom_info;
} pre_pop_t;

typedef struct {
    uint16_t no_pre_pops, max_subpartitions;
    pre_pop_t population_table;
} pre_pop_info_table_t;


address_t synaptogenesis_dynamics_initialise(
    address_t afferent_populations){
    use(afferent_populations);
    return afferent_populations;
}

void synaptogenesis_dynamics_rewire(){
    log_error("There should be no structurally plastic synapses!");
}

address_t synaptogenesis_dynamics_formation_rule(address_t synaptic_row_address){
    use(synaptic_row_address);
    return NULL;
}

address_t synaptogenesis_dynamics_elimination_rule(address_t synaptic_row_address){
    use(synaptic_row_address);
    return NULL;
}