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
It will also generate a `.env` file with new random keys and passwords that the system will use.

If you are deploying on a server you need to configure hosts and other system by editing the `.env` file.

## Start MakerAdmin, web shop, etc.

Run all services locally (but you will have to insert data, see below):
```
make run
```

You can also run in dev mode where source directories are mounted inside the containers and sources are 
reloaded when changed (in most cases):

```
make dev
```

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
mysql> use makeradmin

mysql> insert into membership_group_permissions (group_id, permission_id) select 1, permission_id from membership_permissions where permission != 'service';
Query OK, 25 rows affected (0.04 sec)
Records: 25  Duplicates: 0  Warnings: 0

mysql> update access_tokens set permissions = null where user_id > 0;
Query OK, 2 rows affected (0.02 sec)
Rows matched: 2  Changed: 2  Warnings: 0

mysql> exit
Bye
```

### Adding items to the shop
The file [`backend/src/scrape/tictail.json`](./backend/src/scrape/tictail.json) contains a list of the items that can be bought with attributes. They must be imported to the docker container's database:
```bash
docker-compose exec backend bash -c "cd src/scrape && python tictail2db.py"
```

The docker container corresponding to the webshop must be rebuilt when it is changed (and then imported anew):
```bash
docker-compose up -d --build webshop
```

### Viewing MakerAdmin etc.
Go to:
* [the makeradmin web site](http://localhost:8009)
* [the web shop](http://localhost:8011/shop)

### Frontend js dev-server
To run a webpack-dev-server inside a docker container (will node, npm
and node_modules inside the image and mount js source files from local
file system).

```make admin-dev-server```
Then go to:
* (http://localhost:8080)

## Tests

### Function test that requires a running installation

Function tests are written in python and the sources for the tests are in the test directory. There are 
tests using the api gateway as well as selenium tests. Those tests are also run in travis.

You can run the tests in test containers using a one off db with:
```
make test
```

Or you can run against your local running environment with:
```
make dev-test
```

And you can also run single tests against your local running environment using you favorite test
runner (like pytest).

### Javascript unit tests

Javascript unit tests are run when the images is build but they can also be run against the source directly
by ```make test-admin-js``` or ```npm --prefix admin run test```.



