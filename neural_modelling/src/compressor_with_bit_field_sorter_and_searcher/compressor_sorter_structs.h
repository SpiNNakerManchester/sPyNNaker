#ifndef __COMPRESSOR_SORTER_STRUCTS_H__


typedef struct comp_core_store_t{
    // how many rt tables used here
    uint32_t n_elements;
    // how many bit fields were used to make those tables
    uint32_t n_bit_fields;
    // compressed table location
    address_t compressed_table;
    // elements
    address_t * elements;
} comp_core_store_t;

//! \brief struct for bitfield by processor
typedef struct _bit_field_by_processor_t{
    // processor id
    uint32_t processor_id;
    // length of list
    uint32_t length_of_list;
    // list of addresses where the bitfields start
    address_t* bit_field_addresses;
} _bit_field_by_processor_t;

//! \brief struct for processor coverage by bitfield
typedef struct _proc_cov_by_bitfield_t{
    // processor id
    uint32_t processor_id;
    // length of the list
    uint32_t length_of_list;
    // list of the number of redundant packets from a bitfield
    uint32_t* redundant_packets;
} _proc_cov_by_bitfield_t;

//! \brief struct for figuring keys from bitfields, used for removal tracking
typedef struct proc_bit_field_keys_t{
    // processor id
    uint32_t processor_id;
    // length of the list
    uint32_t length_of_list;
    // list of the keys to remove bitfields for.
    uint32_t* master_pop_keys;
} proc_bit_field_keys_t;

//! \brief struct for n redundant packets and the bitfield addresses of it
typedef struct coverage_t{
    // n redundant packets
    uint n_redundant_packets;
    // length of list
    uint32_t length_of_list;
    // list of corresponding processor id to the bitfield addresses list
    uint32_t* processor_ids;
    // list of addresses of bitfields with this x redundant packets
    address_t* bit_field_addresses;
} coverage_t;

//! \brief struct holding keys and n bitfields with key
typedef struct master_pop_bit_field_t{
    // the master pop key
    uint32_t master_pop_key;
    // the number of bitfields with this key
    uint32_t n_bitfields_with_key;
} master_pop_bit_field_t;

//! \brief struct address_region_data
typedef struct address_region_data_t{
    // the bitfield address
    address_t bit_field_address;
    // the address of the key atom map
    address_t incoming_key_atom_map_address;
    // the processor id corresponding to
    uint32_t processor_id;
} address_region_data_t;

//! \brief uncompressed routing table region
typedef struct uncompressed_table_region_data_t{
    // the app id
    uint32_t app_id;
    // table struct
    table_t uncompressed_table;
} uncompressed_table_region_data_t;

//! \brief compressor core data region
typedef struct compressor_cores_region_data_t{
    // how many compressor cores
    uint32_t n_compressor_cores;
    // the processor ids
    uint32_t* processor_ids;
} compressor_cores_region_data_t;

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
    key_atom_entry_t* maps;
} key_atom_data_t;

//! \brief bitfield data region
typedef struct bit_field_region_data_t{
    // bit field master pop key
    uint32_t key;
    // n words representing the bitfield
    uint32_t n_words;
    // the words of the bitfield
    uint32_t* words;
} bit_field_region_data_t;

//! \brief addresses top level struct
typedef struct addresses_top_level_t{
    // threshold of how many bitfields to add before a success
    uint32_t threshold_for_success;
    // how many sets of addresses there are.
    uint32_t n_address_triples;
    // list of triples
    address_region_data_t* regions;
} addresses_top_level_t;



#define __COMPRESSOR_SORTER_STRUCTS_H__
#endif  // __COMPRESSOR_SORTER_STRUCTS_H__