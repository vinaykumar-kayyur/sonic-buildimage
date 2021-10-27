obj-m := genl-packet.o

EXTRA_CFLAGS := -I$(src)/include

KVERSION ?= $(shell uname -r)
KDIR ?= /lib/modules/$(KVERSION)/build

default:
	$(MAKE) -C $(KDIR) M=$$PWD modules

clean:
	$(MAKE) -C $(KDIR) M=$$PWD clean

.PHONY: default clean