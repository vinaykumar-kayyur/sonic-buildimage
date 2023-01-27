OBJS = $(patsubst $(SRC_TOP_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRCS)) $(EXTRA_OBJS)

ifeq ($(IS_GCOV),yes)
CPPFLAGS += -fprofile-arcs -ftest-coverage
endif

LIBS = $(LIB_DIR)/lib$(LIB).a

$(LIBS): $(OBJS)
	@echo "LIB => $@" && \
	if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi && \
	rm -rf $@ && \
	$(AR) $@ $^ && \
	$(RANLIB) $@

.PHONY: clean
clean:
	rm -rf $(LIB_DIR)/lib$(LIB).a $(OBJS) $(EXTRA_CLEANS)

include $(MK_DIR)/obj.mk
