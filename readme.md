[![Build Status](https://travis-ci.org/makerspace/makeradmin.svg?branch=master)](https://travis-ci.org/makerspace/makeradmin)
# Makeradmin

## Install 

### Docker
```
sudo apt-get install docker.io docker-compose
sudo adduser your_username docker
```
You need to sign out and sign back in again for changes to take effect. 

### Python
Python 3.6 or higher is required.

### npm
```
sudo apt-get install npm
```

### Dependencies for Python and npm
```bash
make init
```

## Initialize everything
```
make firstrun
```

This will initialize submodules, build docker images and configure the database. This may take quite some time.
It will also generate a .env file with new random keys and passwords that the system will use.

## Start MakerAdmin, web shop, etc.
```
make run
```

At this point MakerAdmin should be up and running but there are no users.

### Add a user that can access MakerAdmin
```
python3 create_user.py --first-name "Maker" --last-name "Makersson" --email "maker@example.com" --type admin
```

To change password for existing user.
```
docker-compose run --rm --no-deps membership /usr/bin/php /var/www/html/artisan member:password <email> <password>
```

### Adding permissions for all users to view data on MakerAdmin
Start up Docker's mysql instance

```
$ ./mysql.sh
```

Add persmissions for users (any that you added above)
```
mysql> use makeradmin-membership

mysql> insert into membership_group_permissions (group_id, permission_id) select 1, permission_id from membership_permissions where permission != 'service';
Query OK, 25 rows affected (0.04 sec)
Records: 25  Duplicates: 0  Warnings: 0

mysql> use makeradmin-apigateway
Database changed
mysql> update access_tokens set permissions = null where user_id > 0;
Query OK, 2 rows affected (0.02 sec)
Rows matched: 2  Changed: 2  Warnings: 0

mysql> exit
Bye
```

### Adding items to the shop
The file [`webshop/src/scrape/tictail.json`](./webshop/src/scrape/tictail.json) contains a list of the items that can be bought with attributes. They must be imported to the docker container's database:
```bash
docker exec -it makeradmin_webshop_1 bash -c "cd scrape && python3 tictail2db.py"
```

The docker container corresponding to the webshop must be rebuilt when it is changed (and then imported anew):
```bash
docker-compose up -d --build webshop
```

### Viewing MakerAdmin etc.
Go to:
* [the makeradmin web site](http://localhost:8009)
* [the web shop](http://localhost:8010/shop)

### Frontend js dev-server
To run a webpack-dev-server inside a docker container (will node, npm
and node_modules inside the image and mount js source files from local
file system).

```make frontend-dev-server```
Then go to:
* (http://localhost:8080)

