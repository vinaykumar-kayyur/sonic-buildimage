OBJS = $(patsubst $(SRC_TOP_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS)) $(EXTRA_OBJS)

#add by zzhu for gcov
ifeq ($(IS_GCOV),yes)
CPPFLAGS += -fprofile-arcs -ftest-coverage
LD_LIBS += -fprofile-arcs
endif

$(BIN_DIR)/$(PROG): $(OBJS) $(DEP_LIBS)
	@echo "LD  => $@" && \
	if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi && \
	$(CC) $(LD_FLAGS) -o $@ $(OBJS) $(LD_LIBS)

.PHONY: clean
clean:
	rm -rf $(BIN_DIR)/$(PROG) $(OBJS) $(EXTRA_CLEANS)

include $(MK_DIR)/obj.mk
