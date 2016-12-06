TODO:

Bygga om Mail så att den hämtar member via API

Flytta över filer från gamla installation
Skrota konstiga relationer mellan member och group
Inte duplicera Traits, Entity
Flytta traits till controller?
Skicka callbacks och andra events när det händer saker
Ta bort user modell
Rensa igenom gammalt skräp

X-Forwarded-For

API:
	Ping
	Alive?
	Version



Installation
============

Create database
-----------------

Create a new database

CREATE USER `makeradmin-membership`@'%' IDENTIFIED BY 'g34Api5C9L';
CREATE DATABASE `makeradmin-membership`;
GRANT ALL ON `makeradmin-membership`.* TO `makeradmin-membership`@'%';
FLUSH PRIVILEGES;


# Build docker container
./docker_build


# Start docker container
# ./docker/docker_run mysql makeradmin-membership g34Api5C9L makeradmin-membership api.makeradmin.dev
./docker/docker_run mysql makeradmin-membership g34Api5C9L makeradmin-membership makeradmin-apigateway

Create an admin user
--------------------
./artisan member:create username password


Register service
----------------
Register the service to the API Gateway
./artisan service:register



APIGATEWAY="makeradmin-apigateway"