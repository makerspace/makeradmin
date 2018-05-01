# Makeradmin
==========

### Install dependencies 
`sudo apt-get install docker.io docker-compose`<br />
`sudo adduser your_username docker`<br />
You need to sign out and sign back in again for changes to take effect. 

### Initialize everything
`make firstrun`

This will initialize submodules, build docker images and configure the database. This may take quite some time.
It will also generate a .env file with new random keys and passwords that the system will use.

### Start MakerAdmin 
`make run` 

At this point MakerAdmin should be up and running but there are no users.<br />

`python3 create_user.py --first-name "Maker" --last-name "Makersson" --email "maker@example.com" --type admin`

To change password for existing user.<br />
`docker-compose run --rm --no-deps membership /usr/bin/php /var/www/html/artisan member:password <email> <password>`
