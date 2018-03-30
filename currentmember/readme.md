Current Member Service
======================

This service provides routes to get and update info for the member that is currently logged in and a few routes related to that.

It essentially acts as a proxy for the membership module.

- `user.py` contains the code specific to this service.
- `service.py` is a small generic module for makeradmin microservices. It handles registering the microservice, reading the configuration, connecting to the databse and some utility methods for communicating with other services.
