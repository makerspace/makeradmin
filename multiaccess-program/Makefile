
init:
	pip install -r requirements.txt --upgrade

test:
	nosetests test

dist-sync:

dist-export:
	docker run -it --rm -v $(shell pwd):/src cdrx/pyinstaller-windows:python3 "/usr/bin/pyinstaller --onefile --clean -y --dist ./dist --workpath /tmp multi_access_export.spec; chown -R --reference=. ./dist ./destroyer"

dist: dist-sync dist-export

clean:
	rm -rf dist build
	find src -name __pycache__ -prune -type d -exec rm -rf {} \;

.PHONY: init test clean dist dist-sync dist-export

