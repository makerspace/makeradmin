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

.env:
	python3 create_env.py

stop:
	@ # At first stop all containers that need to unregister (all but db2 and api-gateway)
	@ docker-compose stop -t 30 frontend 
	@ docker-compose stop -t 30 messages
	@ docker-compose stop -t 30 email-dispatcher
	@ docker-compose stop -t 30 multiaccesssync
	@ docker-compose stop -t 30 sales
	@ docker-compose stop -t 30 economy
	@ docker-compose stop -t 30 current-member
	@ docker-compose stop -t 30 rfid
	@ docker-compose stop -t 30 membership
	docker-compose down

firstrun:
	make update
	make .env
	make build
	make init-db
	echo "\033[31mRun 'make run' to start MakerAdmin\033[0m"