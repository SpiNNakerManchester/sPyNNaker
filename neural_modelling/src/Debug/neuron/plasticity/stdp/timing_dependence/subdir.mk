################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_pair_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_pfister_triplet_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_recurrent_fixed_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_recurrent_pre_stochastic_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_recurrent_stochastic_impl.c \
../neuron/plasticity/stdp/timing_dependence/timing_vogels_2011_impl.c 

OBJS += \
./neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_pair_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_pfister_triplet_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_fixed_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_pre_stochastic_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_stochastic_impl.o \
./neuron/plasticity/stdp/timing_dependence/timing_vogels_2011_impl.o 

C_DEPS += \
./neuron/plasticity/stdp/timing_dependence/timing_nearest_pair_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_pair_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_pfister_triplet_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_dual_fsm_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_fixed_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_pre_stochastic_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_recurrent_stochastic_impl.d \
./neuron/plasticity/stdp/timing_dependence/timing_vogels_2011_impl.d 


# Each subdirectory must supply rules for building sources it contributes
neuron/plasticity/stdp/timing_dependence/%.o: ../neuron/plasticity/stdp/timing_dependence/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


