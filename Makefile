include ../Gadgetron/dev.make

.PHONY: test
test:
	python -m unittest discover

.PHONY: clean
clean:
	rm -rf test/placed*.brd
	rm -rf test/routed*.brd
	rm -rf test/*.job
	rm -rf test/*.pro
	rm -rf test/*.pyc