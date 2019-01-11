CC = gcc
AR = ar
# CFLAGS = -Wall -W -Wunused -lpthread -g -O2 -ggdb -DIPMI_PRJ -DDIAG_DEBUG -DDIAG_API -DHAVE_CONFIG_H -DFCS_CTRL_NO_BURST -DFCS_DEBUG -DHAVE_NANOSLEEP
CFLAGS = -Wall -W -Wunused -lpthread -g -O0 -ggdb -DDIAG_DEBUG -DDIAG_API -DHAVE_CONFIG_H -DFCS_DEBUG -DHAVE_NANOSLEEP
LFLAGS = -lm -pthread 
DEL_FILE = rm -f
MV_FILE = mv -f
OBJ_FILE_NODE = ./*.o
#VPATH = 
INCPATH     =     -I../include/
TARGET   = ispvm
# OBJECTS += cpld_ops.o i2c_dev.o i2c_chips.o sys_eeprom.o crc32.o bsp_ifc.o hpcsfp.o smartfan.o test.o path.o

OBJECTS += hardware.o ispvm_ui.o ivm_core.o

.c.o:
	$(CC) -c $(CFLAGS) $(INCPATH) -o $@ $<
$(TARGET):$(OBJECTS) 
	$(CC) -o $(TARGET) $(OBJECTS)
	
clean:
	-$(DEL_FILE) $(TARGET)
	-$(DEL_FILE) $(OBJ_FILE_NODE)


