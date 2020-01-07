COMMON_DIR   := ../../common
COMMON_OBJS  := $(COMMON_DIR)/ipmi_util.o
EXTRA_CFLAGS += -I$(obj)/$(COMMON_DIR)

obj-m := insp_sc5630el_psu.o insp_sc5630el_sfp.o insp_sc5630el_eeprom.o inspur_sc5630el_platform.o inspur-pca9641.o inspur_psu.o inspur_sc5630el_cpld.o inspur_sc5630el_optoe.o inspur_sc5630el_sfpio.o
insp_sc5630el_psu-objs := inspur_sc5630el_psu.o $(COMMON_OBJS)
insp_sc5630el_sfp-objs := inspur_sc5630el_sfp.o $(COMMON_OBJS)
insp_sc5630el_eeprom-objs := inspur_sc5630el_eeprom.o $(COMMON_OBJS)
