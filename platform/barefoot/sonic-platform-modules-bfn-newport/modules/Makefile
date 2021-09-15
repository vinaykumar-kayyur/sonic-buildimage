
ifneq ($(KERNELRELEASE),)
ccflags-y=-I$(src)/i2c

obj-m := bf_fpga.o bf_switch_sysfs.o bf_fan.o bf_xcvr.o bf_sensor.o \
			bf_syseeprom.o bf_psu.o bf_fpga_swi.o bf_watchdog.o
bf_switch_sysfs-y := switch_interface/bf_switch_sysfs.o
bf_fan-y := switch_interface/bf_fan_driver.o \
			switch_interface/bf_fan_api.o \
			switch_interface/bf_module_util.o
bf_xcvr-y := switch_interface/bf_xcvr_driver.o \
				switch_interface/bf_xcvr_api.o \
				switch_interface/bf_module_util.o \
				switch_interface/bf_xcvr_optoe.o
bf_sensor-y := switch_interface/bf_sensor_driver.o \
				switch_interface/bf_sensor_api.o \
				switch_interface/bf_module_util.o
bf_syseeprom-y := switch_interface/bf_eeprom_driver.o \
					switch_interface/bf_eeprom_api.o \
					switch_interface/bf_module_util.o
bf_psu-y := switch_interface/bf_psu_driver.o \
			switch_interface/bf_psu_api.o \
			switch_interface/bf_module_util.o
bf_fpga-y := bf_fpga_main.o \
				bf_fpga_ioctl.o \
				bf_fpga_sysfs.o \
				i2c/bf_fpga_i2c.o \
				i2c/bf_fpga_i2c_ctrl.o \
				i2c/bf_fpga_i2c_porting.o \
				i2c/bf_fpga_i2c_util.o
bf_fpga_swi-y := switch_interface/bf_fpga_swi_driver.o \
					switch_interface/bf_fpga_swi_api.o \
					switch_interface/bf_module_util.o
bf_watchdog-y := switch_interface/bf_watchdog_driver.o \
					switch_interface/bf_watchdog_api.o \
					switch_interface/bf_module_util.o

else
ifeq (,$(KERNEL_SRC))
$(error KERNEL_SRC is not defined)
else
KERNELDIR:=$(KERNEL_SRC)
endif
PWD:=$(shell pwd)
default:
	$(MAKE) -C $(KERNELDIR)  M=$(PWD) modules
clean:
	rm -rf *.o *.mod.o *.mod.o *.ko .*cmd .tmp_versions Module.markers Module.symvers modules.order
endif
