%.o: %.c
	@echo "CC  => $@" && \
	if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi && \
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ $<

$(OBJ_DIR)/%.o: $(SRC_TOP_DIR)/%.c
	@echo "CC  => $@" && \
	if [ ! -d $(dir $@) ]; then mkdir -p $(dir $@); fi && \
	$(CC) $(CFLAGS) $(CPPFLAGS) -c -o $@ $<

