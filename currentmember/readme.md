Member Services
=======================

This repository contains a few different services for MakerAdmin.

They use the same repository as they share some common code and sharing it using e.g git submodules is not the most convenient workflow.
They could however if necessary be split up into different repositories.

Current Member
--------------
This service provides routes to get and update info for the member that is currently logged in and a few routes related to that.

It essentially acts as a proxy for the membership module.

- `user.py` contains the code specific to this service.

Webshop
-------
A frontend and backend for a simple makerspace webshop.

Common
------
Contains common code used by several services

- `service.py` is a small generic module for makeradmin microservices. It handles registering the microservice, reading the configuration, connecting to the databse and some utility methods for communicating with other services.
- `migrate.py` is a helper script for migrating database tables based on mygrations (https://github.com/cmancone/mygrations)