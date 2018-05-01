
init:
	python -m pip install -r requirements.txt --upgrade

pep8:
	python -m pycodestyle --ignore=W503,W504,W391,W293,E741,E701,E241,E402 --max-line-length=120 --exclude=.direnv,dist,build,.idea .

test: pep8
	python -m nose test

win-test: 
	python -m nose win-test

all-test: test win-test

dist-sync:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_sync.spec; chown -R --reference=. ./dist ./multi_access"

dist-export:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp specs/multi_access_export.spec; chown -R --reference=. ./dist ./multi_access"

dist: dist-sync dist-export

clean:
	rm -rf dist build
	find . -name __pycache__ -prune -type d -exec rm -rf {} \;

.PHONY: init test clean dist dist-sync dist-export

