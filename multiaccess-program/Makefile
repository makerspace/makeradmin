
init:
	python3 -m pip install pip --upgrade
	python3 -m pip install -r requirements.txt --upgrade

pep8:
	python3 -m pycodestyle --ignore=W503,W504,W391,W293,E741,E701,E241,E402 --max-line-length=120 --exclude=.direnv,dist,build,.idea .

test: pep8
	python3 -m nose test

coverage:
	rm -rf coverage .coverage
	coverage3 run $(shell which nosetests) test
	coverage3 html -d coverage --omit=test*,*.pyenv*
	firefox coverage/index.html

target-test: 
	python3 -m nose test/target

all-test: test target-test

dist-sync:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_sync.spec; chown -R --reference=. ./dist ./multi_access"

dist-export:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_export.spec; chown -R --reference=. ./dist ./multi_access"

dist-dump:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_dump.spec; chown -R --reference=. ./dist ./multi_access"

dist: dist-sync dist-export

clean:
	rm -rf dist build coverage
	find . -name __pycache__ -prune -type d -exec rm -rf {} \;

.PHONY: init test clean dist dist-sync dist-export coverage

