TARGET:= pddf_custom_fan_driver_module
$(TARGET)-objs := ./fan_driver/pddf_custom_fan_api.o ./fan_driver/pddf_custom_fan_driver.o

TARGET1:= pddf_custom_led_module
$(TARGET1)-objs := ./led_driver/pddf_custom_led_module.o

obj-m := $(TARGET).o $(TARGET1).o
obj-m += pddf_custom_fpga_algo.o pddf_custom_fpga_extend.o pddf_custom_psu.o tps536c7.o
