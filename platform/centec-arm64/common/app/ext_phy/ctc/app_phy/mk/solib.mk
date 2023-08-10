CFLAGS += -fpic
OBJS = $(patsubst %.c,$(OBJ_DIR)/%.o,$(SRCS)) $(EXTRA_OBJS)

$(LIB_DIR)/lib$(LIB).so: $(OBJS)
	@echo "LIB => $@" && \
	if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi && \
	$(CC) -shared -o $@ $^

.PHONY: clean
clean:
	rm -rf $(LIB_DIR)/lib$(LIB).so $(OBJS) $(EXTRA_CLEANS)

include $(MK_DIR)/obj.mk
