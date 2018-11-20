
build: .env
	docker-compose build

run: .env
	docker-compose up

dev: .env
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

test: .env
	docker-compose -p test -f docker-compose.yml -f docker-compose.test.yml down || true
	docker-compose -p test -f docker-compose.yml -f docker-compose.test.yml up --build --abort-on-container-exit

init-npm:
	cd admin && npm install 
	cd public && npm install 

init-pip:
	python3 -m pip install --upgrade -r requirements.txt

init: init-pip init-npm

init-db: .env
	python3 db_init.py

insert-devel-data: .env
	docker exec -it makeradmin_backend_1 bash -c "cd /work/src/scrape && python3 tictail2db.py"

.env:
	python3 create_env.py

stop:
	docker-compose down

test-admin-js:
	npm --prefix admin run eslint
	npm --prefix admin run test

firstrun: .env build init-db
	echo -e "\e[31mRun 'make run' to start MakerAdmin\e[0m"

admin-dev-server:
	mkdir -p admin/node_modules
	docker-compose -f admin/dev-server-compose.yaml rm -sfv
	docker volume rm -f makeradmin_node_modules
	docker-compose -f admin/dev-server-compose.yaml up --build

.PHONY: build firstrun admin-dev-server init init-db init-npm init-pip install run stop test dev
