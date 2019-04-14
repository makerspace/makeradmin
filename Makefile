
COMPOSE=docker-compose
TEST_COMPOSE=docker-compose -p test -f docker-compose.yml -f docker-compose.test.yml
DEV_COMPOSE=docker-compose -f docker-compose.yml -f docker-compose.dev.yml

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
	docker-compose down
	docker volume rm -f makeradmin_dbdata
	docker volume rm -f makeradmin_logs
	docker volume rm -f makeradmin_node_modules
	docker volume rm -f test_dbdata
	docker volume rm -f test_logs

dev-test:
	(cd api/src && python3 -m pytest --workers auto -ra)

init-npm:
	cd admin && npm install 
	cd public && npm install 

init-pip:
	python3 -m pip install --upgrade -r requirements.txt

init: init-pip init-npm

insert-devel-data: .env
	docker-compose run backend bash -c "cd /work/src/scrape && python3 tictail2db.py"

.env:
	python3 create_env.py

stop:
	$(COMPOSE) down

test-admin-js:
	npm --prefix admin run eslint
	npm --prefix admin run test

firstrun: .env build
	$(COMPOSE) run api python3 ./firstrun.py

.PHONY: build firstrun init init-npm init-pip install run stop dev-test test-clean test dev
