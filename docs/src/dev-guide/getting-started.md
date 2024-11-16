# Getting Started

## Dependencies

### Docker

On a Debian based system (Ubuntu, Linux Mint, etc.), you can install docker with
the package manager:

```bash
sudo apt-get install docker.io
sudo adduser $(whoami) docker
```

You need to sign out and sign back in again for changes to take effect.

### Python

Makeradmin uses Python 3.11.

```bash
sudo apt-get install python3.11-dev python3.11-doc python3-pip
```

### npm

Makeradmin uses nodejs 18 for a few components

```bash
sudo apt-get install npm
```

## Initialize everything

Clone this git repository to a suitable place on your computer / server

!!! tip "Tip: Use a Python virtual environment"

    Start by initializing and activating a [virtual python environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) in the cloned folder.
    This makes sure that the packages used for Makeradmin are isolated into its own "environment" (i.e. in the local directory), and will not interfere with packages already installed.

        $ python3 -m venv .venv
        $ source .venv/bin/activate

Run the firstrun script

```bash
make firstrun
```

This will build docker images and configure the database. This may take quite some time.
It will also generate a `.env` file with new random keys and passwords that the system will use.

You will be prompted for if you want to create a new admin user, it is recommended to do this here.

You will also be prompted for if you want to create some fake members, transactions etc which can be useful for development.

If you are deploying on a server you need to configure hosts and other settings by editing the `.env` file.
If you do modify the `.env` file you need to restart the services afterwards by running

```bash
docker-compose up -d --build
```

## Start MakerAdmin, web shop, etc.

Run all services locally (but you will have to insert data, see below):

```bash
make run
```

You can also run in dev mode where source directories are mounted inside the containers and sources are
reloaded when changed (in most cases):

```bash
make dev
```
