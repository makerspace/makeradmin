update:
	git pull
	git submodule update --init

run:
	docker-compose up

migrate:
	./migrate.sh
