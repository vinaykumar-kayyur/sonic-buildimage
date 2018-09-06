# 
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements. See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership. The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.
# 

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
