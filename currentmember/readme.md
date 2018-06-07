Member Services
=======================

This repository contains a few different services for MakerAdmin.

They use the same repository as they share some common code and sharing it using e.g git submodules is not the most convenient workflow.
They could however if necessary be split up into different repositories.

Current Member
--------------
This service provides routes to get and update info for the member that is currently logged in and a few routes related to that.

It essentially acts as a proxy for the membership module.

- `main.py` contains the code specific to this service.

To see all routes of the service, access the /path/to/service/routes endpoint which will list them all.

Webshop
-------
A frontend and backend for a simple makerspace webshop.

The Docker container starts two scripts, `frontend.py` and `backend.py`.
The frontend hosts the webshop frontend on port 8011 and the backend registers with the
api-gateway as a normal service with the endpoint `webshop`.

To unify this with the rest of the makeradmin frontend a reverse proxy (e.g nginx) needs to be used.

The frontend uses SASS (.scss) stylesheets. These will be automatically compiled when the container starts and additionally if the APP_DEBUG environment variable is 'true' then it will continously watch for changes to the scss files and recompile them whenever they are changed.

To see all routes of the service, access the /path/to/service/routes endpoint which will list them all.

RFID
----
Replacement for the original MakerAdmin-RFID service, but implemented in only a few lines of code.
This module has functionality for updating key dates based on purchases from the webshop module.

Common
------
Contains common code used by several services

- `service.py` is a small generic module for makeradmin microservices. It handles registering the microservice, reading the configuration, connecting to the databse and some utility methods for communicating with other services.
- `migrate.py` is a helper script for migrating database tables. It will look at the .sql files in the database directory and execute them in order. It will store executed migrations in a database table so you can safely run this script multiple times. The MakerAdmin-Hub has functionality for running all migrations scripts in all services, and that will find this script too. Note that the script has to be executed inside a container for it to work. The .sql files need to have numeric names (e.g 1.sql etc.).