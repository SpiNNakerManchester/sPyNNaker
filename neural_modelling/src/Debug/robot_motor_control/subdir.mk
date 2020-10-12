################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../robot_motor_control/robot_motor_control.c 

OBJS += \
./robot_motor_control/robot_motor_control.o 

C_DEPS += \
./robot_motor_control/robot_motor_control.d 


# Each subdirectory must supply rules for building sources it contributes
robot_motor_control/%.o: ../robot_motor_control/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: GCC C Compiler'
	gcc -I"/Users/ghost/git/SpiNNMan/c_models" -I"/Users/ghost/git/spinnaker_tools/include" -I"/Users/ghost/git/SpiNNFrontEndCommon/c_common" -O0 -g3 -Wall -c -fmessage-length=0 -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


