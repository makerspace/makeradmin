# Makeradmin
==========

## This is work in progress and may do absolutely anything or nothing at all
-------------------------------------------------------------------------

### Install dependencies 
`sudo apt-get install docker.io docker-compose`<br />
`sudo adduser your_username docker`<br />
You need to sign out and sign back in again for changes to take effect. 

### Initialize submodules and pull latest commits 
`make update`

### Build docker images 
`make build`

### Create (or migrate) all database tables, (run once) 
`make init-db`

### Configure your MakerAdmin system. 
MakerAdmin requires some variables to be defined for the system to work. These variables are defined in the '.env' file. To create a file with default configuration run<br />
`make create-default-env`

### Start MakerAdmin 
`make run` 

At this point MakerAdmin should be up and running but there are no users.<br />
`docker-compose run --rm --no-deps membership /usr/bin/php /var/www/html/artisan member:create username password`

