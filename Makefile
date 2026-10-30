PYTHON ?= python3
.PHONY: test smoke clean

test:
	PYTHONPATH=. $(PYTHON) -m unittest discover -s tests -v

smoke:
	PYTHONPATH=. $(PYTHON) -m ez8native.asm examples/data_smoke.asm -o build/data_smoke.hex

clean:
	rm -rf build
