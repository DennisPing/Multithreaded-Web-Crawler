.PHONY: webcrawler

webcrawler:
	@if [ -e webcrawler ]; then \
		rm webcrawler; \
	fi;
	@touch webcrawler
	@printf "#!/bin/bash\n" >> webcrawler
	@printf "python3 main.py \$$1 \$$2 \$$3" >> webcrawler
	@chmod +x webcrawler
	$(info Built target program: webcrawler)

clean:
	@if [ -e webcrawler ]; then \
		rm webcrawler; \
	fi;