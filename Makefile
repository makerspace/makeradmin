# Updates submodules to the commits indicated in this repository
update:
	git pull
	git submodule update --init --recursive --remote

build: .env
	docker-compose build

run: .env
	docker-compose up

init-db: .env
	./db_init.sh

create-default-env: .env
	@test -e .env 
.env:
	@cp -n .env.example .env

stop:
	docker-compose down
