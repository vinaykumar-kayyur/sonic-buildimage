TARGET = pddf_psu_driver_module

obj-m := $(TARGET).o 

$(TARGET)-objs := pddf_psu_api.o pddf_psu_driver.o 
#GCOV_PROFILE := y

ccflags-y := -I$(M)/modules/include
#ccflags-y += -I$(M)/modules/psu
