build: .env
	docker-compose build

run: .env
	docker-compose up

init:
	python3 -m pip install --upgrade -r requirements.txt

init-db: .env
	python3 db_init.py

.env:
	python3 create_env.py

stop:
	docker-compose down

firstrun: .env build init-db
	echo "\033[31mRun 'make run' to start MakerAdmin\033[0m"

.PHONY: build init-db
