TARGET = pddf_xcvr_driver_module

obj-m := $(TARGET).o 

$(TARGET)-objs := pddf_xcvr_api.o pddf_xcvr_driver.o
#GCOV_PROFILE := y

ccflags-y := -I$(M)/modules/include
#ccflags-y += -I$(M)/modules/xcvr
