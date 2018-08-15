# SONiC make file

%::
	@echo "+++ --- Making $@ --- +++"
	BLDENV=stretch make -f Makefile.work stretch
	make -f Makefile.work $@

stretch:
	@echo "+++ Making $@ +++"
	BLDENV=stretch make -f Makefile.work stretch

clean reset init configure :
	@echo "+++ Making $@ +++"
	make -f Makefile.work $@
