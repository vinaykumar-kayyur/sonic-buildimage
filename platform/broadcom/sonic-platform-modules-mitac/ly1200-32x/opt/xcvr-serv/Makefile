#/*
#**********************************************************************
#*
#* @filename  Makefile
#*
#* @purpose   This Makefile is used for Lattice utility
#*
#* @create    2017/03/03
#*
#* @author    yencheng.lin <yencheng.lin@mic.com.tw>
#*
#* @history   2017/03/03: init version
#*
#**********************************************************************
#*/

TARGETS    := xcvr-servd
INC = $(wildcard *.h)
OBJ=$(subst .c,.o,$(wildcard *.c))

.PHONY: all
all: $(TARGETS)

.PHONY: config
config:

.PHONY: patch
patch:

.PHONY: install
install:
	mkdir -p $(INST_DIR)/xcvr-serv/
	cp $(TARGETS) $(INST_DIR)/xcvr-serv/

.PHONY: uninstall
uninstall:
	rm -f $(addprefix $(INST_DIR)/xcvr-serv/,$(TARGETS))

.PHONY: clean
clean:
	rm -rf $(OBJ) $(TARGETS)

.PHONY: distclean
distclean: clean

$(OBJ): $(INC)
%.o: %.c
	$(CC) -c -o $@ $< -Wall -Wextra -Werror

$(TARGETS): $(OBJ)
	$(CC) $^ -lrt -pthread -o $@
