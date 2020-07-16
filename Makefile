DIR := ${CURDIR}
all:
	@echo "See Makefile for possible targets!"

dist/*.whl dist/*.tar.gz:
	@echo "Building package..."
	python3 setup.py sdist bdist_wheel

build: dist/*.whl dist/*.tar.gz

install-user: build
	@echo "Installing package to user..."
	pip3 install dist/*.whl

test:
	@echo "Running tests..."
	cd /tmp && python3 -m emzero -i $(DIR)/tests/globv_1.xtsv | diff - $(DIR)/tests/globv_1_emzero.xtsv

install-user-test: install-user test
	@echo "The test was completed successfully!"

ci-test: install-user-test

uninstall:
	@echo "Uninstalling..."
	pip3 uninstall -y emzero

install-user-test-uninstall: install-user-test uninstall

clean:
	rm -rf dist/ build/ emzero.egg-info/

clean-build: clean build
