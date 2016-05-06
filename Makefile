XVFB := $(shell command -v xvfb-run 2> /dev/null)

clean:
	-rm -rf dist coverage 2> /dev/null
	-rm tests.integration.* workbench.log 2> /dev/null

requirements:
	pip install -r requirements/base.txt
	pip install -e .

test-requirements:
	pip install -r requirements/test.txt

quality-requirements:
	pip install -r requirements/quality.txt

js-requirements:
	npm install

setup-sdk:
	./install_sdk.sh

setup-self:
	python setup.py sdist && pip install dist/xblock-dalite-0.1.tar.gz

test: setup-sdk test-requirements test_fast

test_fast:
ifdef XVFB
	xvfb-run --server-args="-screen 0, 1920x1080x24" ./run_tests.py --with-coverage --cover-package=dalite_xblock
else
	./run_tests.py --with-coverage --cover-package=dalite_xblock
endif
	coverage html

diff-cover:
	coverage xml -o coverage/py/cobertura/coverage.xml
	diff-cover --compare-branch=master coverage/py/cobertura/coverage.xml

quality: quality-requirements quality_fast

quality_fast:
	prospector

coverage-report:
	coverage report -m

.PHONY: clean requirements test-requirements quality-requirements setup-self js-requirements test quality coverage-report