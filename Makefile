# Updates submodules to the commits indicated in this repository
update:
	git pull
	git submodule update --init --recursive

# Updates submodules to the latest versions from their respective remotes
force-update:
	git pull
	git submodule update --init --recursive --remote

build:
	docker-compose build

run:
	docker-compose up

migrate:
	./migrate.sh
