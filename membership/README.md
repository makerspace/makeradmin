Membership service
==================
This is a module to keep track of members, groups, permissions, roles and authentication in the MakerAdmin system. This module is required by the API gateway. The reason the functionallity is splittet into a separate service is because 1) we want to keep the API gateway as minimal as possible to be able to hot swap modules without bringing down the system and 2) we want to be able to replace this module with a module with a different backend, like LDAP or similar.

Installation
============
The following guide will help you install the Membership module. Before installning this module you should make sure the API Gateway module is up and runing, as this is required to be able to run other services in the system.

# Requirements
* A working MySQL server
* The API Gateway should already be up and running

# Step 1: Download the source code from GitHub
```
git clone https://github.com/MakersOfSweden/MakerAdmin-Membership
cd ./MakerAdmin-Frontend/docker/
```

# Step 2: Create a database
Create a new database and user in your MySQL database server. 

```
CREATE USER `makeradmin-membership`@'%' IDENTIFIED BY 'password';
CREATE DATABASE `makeradmin-membership`;
GRANT ALL ON `makeradmin-membership`.* TO `makeradmin-membership`@'%';
FLUSH PRIVILEGES;
```

# Step 3: Build docker container
The following script will build a new docker container and tag it with the correct name and version.
```
./docker_build
```

# Step 4: Start docker container
You can now start an instance of the Membership module and register it in the MakerAdmin system. Make sure you specify the database credentials specified in step 2. The last parameter should be the address to the API gateway. Keep in mind that this is the hostname provided by Docker, so it should be the same as the name of the container.
```
./docker_run mysql makeradmin-membership password makeradmin-membership makeradmin-apigateway
```

# Step 5: Create database tables
To create the database table you have to run the migration scripts.
```
./artisan migrate
```

# Step 6: Create an admin user
To be able to login for the first time you have to create an administrator user. This is done from the command line.
```
./artisan member:create username password
```

# Step 7: Test the service
The service should now be up and running and should be possible to access from the API.