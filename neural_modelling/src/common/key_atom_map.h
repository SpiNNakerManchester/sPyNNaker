#ifndef __KEY_ATOM_MAP_H__

//! \brief struct for key and atoms
typedef struct key_atom_entry_t{
    // key
    uint32_t key;
    // n atoms
    uint32_t n_atoms;
} key_atom_entry_t;

//! \brief key atom map struct
typedef struct key_atom_data_t{
    // how many key atom maps
    uint32_t n_maps;
    // the list of maps
    key_atom_entry_t maps[];
} key_atom_data_t;

typedef enum key_atom_map_sdram_elements{
    N_MAPS = 0, START_OF_MAPS = 1,
}key_atom_map_sdram_elements;

#define __KEY_ATOM_MAP_H__
#endif  // __KEY_ATOM_MAP_H__