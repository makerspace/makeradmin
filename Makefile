
COMPOSE=docker compose
TEST_COMPOSE=docker compose -p test -f docker-compose.yml -f docker-compose.test.yml
DEV_COMPOSE=docker compose -f docker-compose.yml -f docker-compose.dev.yml
PYTEST_PARAMS?=

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
	(cd api/src && python3 -m pytest --workers auto -ra $(PYTEST_PARAMS))

init-npm:
	cd admin && npm ci
	cd public && npm ci

init-pip:
	python3 -m pip install --upgrade -r requirements.txt

init: init-pip init-npm

.env:
	python3 create_env.py

stop:
	$(COMPOSE) down

test-admin-js:
	npm --prefix admin run eslint
	npm --prefix admin run test

firstrun: .env init build
	$(COMPOSE) run api python3 ./firstrun.py

format: format-python format-webstuff
format-python:
	ruff format .
format-webstuff:
	npx prettier --write --cache .

.PHONY: build firstrun init init-npm init-pip install run stop dev-test
.PHONY: test-clean test dev format format-python format-webstuff
