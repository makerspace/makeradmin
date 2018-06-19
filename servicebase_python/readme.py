Common
------
Contains common code used by several services

- `service.py` is a small generic module for makeradmin microservices. It handles registering the microservice, reading the configuration, connecting to the databse and some utility methods for communicating with other services.
- `migrate.py` is a helper script for migrating database tables. It will look at the .sql files in the database directory and execute them in order. It will store executed migrations in a database table so you can safely run this script multiple times. The MakerAdmin-Hub has functionality for running all migrations scripts in all services, and that will find this script too. Note that the script has to be executed inside a container for it to work. The .sql files need to have numeric names (e.g 1.sql etc.).