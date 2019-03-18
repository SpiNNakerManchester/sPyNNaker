#ifndef __FILTER_INFO_H__

//! \brief the elements in a filter info (bitfield wrapper)
typedef struct filter_info_t{
    uint32_t bit_field_base_key;
    uint32_t bit_field_n_words;
    bit_field_t bit_field;
} filter_info_t;

//! \brief the elements in the bitfield region
typedef struct bit_field_region_t{
    uint32_t n_filter_infos;
    filter_info_t** filters;
} bit_field_region_t;



#define __FILTER_INFO_H__
#endif  // __FILTER_INFO_H__