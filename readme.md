Makeradmin
==========

This is work in progress and may do absolutely anything or nothing at all
-------------------------------------------------------------------------

~~~
# Install dependencies
sudo apt-get install docker.io docker-compose

# clone this repository...
cd repository
make update
#Build docker images
make build
# To create (or migrate) all database tables, (run once)
make migrate

#Start MakerAdmin
make run

~~~
