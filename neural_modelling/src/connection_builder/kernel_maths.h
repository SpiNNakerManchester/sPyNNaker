#pragma once

#include <cstdint>

namespace ConnectionBuilder
{
namespace KernelMaths
{

uint16_t uidiv(uint16_t dividend, uint16_t divider, uint16_t &reminder);

void post_in_pre_world(uint16_t in_row, uint16_t in_col,
                       uint16_t start_row, uint16_t start_col,
                       uint16_t step_row, uint16_t step_col,
                       uint16_t &out_row, uint16_t &out_col);

void pre_in_post_world(uint16_t in_row, uint16_t in_col,
                       uint16_t start_row, uint16_t start_col,
                       uint16_t step_row, uint16_t step_col,
                       int16_t &out_row, int16_t &out_col);


}//namespace KernelMaths
}//namespace ConnectionBuilder