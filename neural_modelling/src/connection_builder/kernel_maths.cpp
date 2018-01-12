#include "kernel_maths.h"
#include "rig_cpp_common/log.h"


uint16_t ConnectionBuilder:: KernelMaths:: uidiv(uint16_t dividend, uint16_t divider,
                                                uint16_t &reminder){
  if(dividend == 0 || dividend < divider){
    reminder = dividend;
    return 0;
  }

  uint16_t d = 0;
  reminder = dividend;
  while(reminder >= divider){
    d += 1;
    reminder -= divider;
  }
  return d;
}

void ConnectionBuilder:: KernelMaths:: post_in_pre_world(uint16_t in_row, uint16_t in_col,
                                                   uint16_t start_row, uint16_t start_col,
                                                   uint16_t step_row, uint16_t step_col,
                                                   uint16_t &out_row, uint16_t &out_col){
  out_row = start_row + in_row*step_row;
  out_col = start_col + in_col*step_col;
}

void ConnectionBuilder:: KernelMaths:: pre_in_post_world(uint16_t in_row, uint16_t in_col,
                                                   uint16_t start_row, uint16_t start_col,
                                                   uint16_t step_row, uint16_t step_col,
                                                   int16_t &out_row, int16_t &out_col){
  int16_t d = (int16_t)(in_row - start_row - 1);
  uint16_t r;
  if ( d == 0 ){
    out_row = 1;
  }
  else if (d < 0) {
    d = (int16_t)uidiv( (uint16_t)(-d), step_row, r );
    out_row = (-d + 1);
  }
  else{
    d = (int16_t)uidiv( (uint16_t)(d), step_row, r );
    out_row = (d + 1);
  }


  d = (int16_t)(in_col - start_col - 1);
  if ( d == 0 ){
    out_col = 1;
  }
  else if (d < 0) {
    d = (int16_t)uidiv( (uint16_t)(-d), step_col, r );
    out_col = (-d + 1);
  }
  else{
    d = (int16_t)uidiv( (uint16_t)(d), step_col, r );
    out_col = (d + 1);
  }

  //out_col = (( (in_col - start_col - 1)/step_col ) + 1);
}