### Makeradmin
==========

This is work in progress and may do absolutely anything or nothing at all
-------------------------------------------------------------------------

~~~
# Install dependencies
sudo apt-get install docker.io docker-compose
sudo adduser your_username docker

# Initialize submodules and pull latest commits
`make update`

# Build docker images
`make build`

# Create (or migrate) all database tables, (run once)
`make init-db`

#Start MakerAdmin
`make run`

At this point MakerAdmin should be up and running but there are no users.
`docker-compose run --rm --no-deps membership /usr/bin/php /var/www/html/artisan member:create username password`

~~~
