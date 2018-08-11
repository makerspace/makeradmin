PY_SOURCE_FILES=$(shell find . -type f -name "*.py")
UNAME_S=$(shell uname -s)

build:
	echo "source_revision = '$(shell git rev-parse --short HEAD)$(shell if ! git diff-index --quiet HEAD --; then echo -dirty; fi)'" > source_revision.py

init:
ifeq ($(UNAME_S),Darwin)
	brew install unixodbc
endif
	python3 -m pip install pip --upgrade
	python3 -m pip install -r requirements.txt --upgrade

pep8:
	python3 -m pycodestyle --ignore=W503,W504,W391,W293,E741,E701,E241,E402 --max-line-length=120 --exclude=.direnv,dist,build,.idea .

test: build pep8
	python3 -m nose test

.coverage: $(PY_SOURCE_FILES)
	coverage3 run --omit="test*,*.pyenv*,*/site-packages/*,*/nosetests"--omit="test*,*.pyenv*,*/site-packages/*,*/nosetests" $(shell which nosetests) test
coverage: .coverage

show-coverage: coverage
	coverage3 html -d coverage
	firefox coverage/index.html

target-test: 
	python3 -m nose test/target

all-test: test target-test

dist-sync: build
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_sync.spec; chown -R --reference=. ./dist ./multi_access"

dist-export: build
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_export.spec; chown -R --reference=. ./dist ./multi_access"

dist-dump: build
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_dump.spec; chown -R --reference=. ./dist ./multi_access"

dist: dist-sync dist-export dist-dump

clean:
	rm -rf dist build .coverage coverage source_revision.py
	find . -name __pycache__ -prune -type d -exec rm -rf {} \;

.PHONY: init test clean dist dist-sync dist-export coverage

