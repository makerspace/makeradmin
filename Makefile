
COMPOSE=docker compose
TEST_COMPOSE=docker compose -p test -f docker-compose.yml -f docker-compose.test.yml
DEV_COMPOSE=docker compose -f docker-compose.yml -f docker-compose.dev.yml
PYTEST_PARAMS?=
PYTHON_VENV=.pydevproject
PYTHON=$(PYTHON_VENV)/bin/python

-include local.mk

build: .env
	$(COMPOSE) build

run: .env
	$(COMPOSE) up

dev: .env
	$(DEV_COMPOSE) up --build

test-clean: .env
	$(TEST_COMPOSE) down -v --remove-orphans || true

test: .env test-clean
	$(TEST_COMPOSE) build
	$(TEST_COMPOSE) up --abort-on-container-exit --exit-code-from test

clean-nuke:
	echo "Removing all databases"
	$(COMPOSE) down
	docker volume rm -f makeradmin_dbdata
	docker volume rm -f makeradmin_logs
	docker volume rm -f makeradmin_node_modules
	docker volume rm -f test_dbdata
	docker volume rm -f test_logs

dev-test:
	(cd api/src && $(PYTHON) -m pytest --workers auto -ra $(PYTEST_PARAMS))

init-npm:
	cd admin && npm install 
	cd public && npm install 

init-venv:
	python3 -m venv $(PYTHON_VENV)

init-pip:
	$(PYTHON) -m pip install -v wheel
	$(PYTHON) -m pip install --no-build-isolation -v "cython<3.0.0" pyyaml==5.4.1 # PyYaml has a bug in their latest build with cython3...
	$(PYTHON) -m pip install -r requirements.txt

init: init-pip init-npm

.env:
	$(PYTHON) create_env.py

stop:
	$(COMPOSE) down

test-admin-js:
	npm --prefix admin run eslint
	npm --prefix admin run test

firstrun: init-venv .env init build
	$(COMPOSE) run api python3 ./firstrun.py

.PHONY: build firstrun init init-npm init-pip install run stop dev-test test-clean test dev
