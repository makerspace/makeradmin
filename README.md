[![Build and run tests for makeradmin](https://github.com/makerspace/makeradmin/actions/workflows/makeradmin.yml/badge.svg)](https://github.com/makerspace/makeradmin/actions/workflows/makeradmin.yml)

# Makeradmin

Member management system for makerspaces. Built by [Stockholm Makerspace](https://makerspace.se).

<img src="docs/src/images/member_list.png" alt="member list" width="400"/>

## Features

### Easily administrate members of the makerspace

-   Name, address, etc.
-   Membership status
-   Access groups and permissions
-   Automatic emails about membership renewal and similar.

<img src="docs/src/images/member_view.png" alt="member view" width="400"/>

### Membership portal

Members get their own portal where they can easily:

-   Check their membership status.
-   Buy additional membership, or even subscribe for automatic membership renewal.
-   Buy other things in a built-in webshop.
-   Take quizzes to improve their knowledge

<img src="docs/src/images/member_portal_front.png" alt="member portal" width="400"/>

### Webshop

MakerAdmin has a webshop that can be used to sell everything from drill bits to membership months.

We use **Stripe** as our payment processor.

<img src="docs/src/images/member_portal_shop.png" alt="member portal shop" width="400"/>

### Clean registration flow

With a clean registration flow, members can more easily sign up, and understand what a makerspace entails.

<img src="docs/src/images/registration_flow.png" alt="registration flow" width="400"/>

### Statistics

Get key insights for how to improve the makerspace.

-   Integrates with the webshop.
-   Integrates with the membership system.
-   Integrates with the quizzes.
-   Integrates with [Accessy](https://accessy.se) for tracking visits to the space.

<img src="docs/src/images/statistics_sales.png" alt="sales statistics" width="400"/>

## Installation

First, you'll need some dependencies.

### Docker

```bash
sudo apt-get install docker.io
sudo adduser $(whoami) docker
```

You need to sign out and sign back in again for changes to take effect.

#### Docker Compose plugin

Follow the instructions on <https://docs.docker.com/compose/install/linux/>

And then verify that you have version 2 of the plugin:

```bash
docker compose version
# Should print something like
# Docker Compose version v2.32.4
```

### Python

Makeradmin uses Python 3.11.

```bash
sudo apt-get install python3.11-dev python3.11-doc python3-pip
```

### npm

```bash
sudo apt-get install npm
```

## Initialize everything

Clone this git repository to a suitable place on your computer / server

> [!TIP]
> Start by initializing and activating a [virtual python environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) in the cloned folder.
> This makes sure that the packages used for Makeradmin are isolated into its own "environment" (i.e. in the local directory), and will not interfere with packages already installed.
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> ```

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
docker compose up -d --build
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

### Adding new users that can access MakerAdmin

This can be done from the web UI, but it can be convenient to do it from the commandline too

```
python3 create_user.py --first-name "Maker" --last-name "Makersson" --email "maker@example.com" --type admin
```

Before running the command above you might have to run the commande below to install all dependencies.

```
make init
```

### Adding permissions for all users to view data on MakerAdmin

If the admins don't seem to have the permissions that they should have (possibly because you have upgraded makeradmin to a newer version)
then you might have to update the permissions. Simply running the firstrun script again will do this:

```bash
make firstrun
```

### Viewing MakerAdmin etc.

Go to:

-   [the makeradmin web site](http://localhost:8009)
-   [the web shop](http://localhost:8011/shop)

### Logging in

Go to [the member page](http://localhost:8011/member) and fill in the email address corresponding to the user created previously. A link will then be printed in the terminal (where `make dev` is run) that allows you to login. E.g.

```
[...]
public_1            | 10.0.2.2 - - [18/Dec/2018:20:50:23 +0000] "GET / HTTP/1.1" 302 223 "http://localhost:8011/member/login/XHCgGQZGrjuG6bO7TVPkikTfQVRo6Eqn?redirect=%2Fmember" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
[...]
```

### Required membership products

Some pages need special products in order to function (e.g. the registration page, or the member page). The products can be created using `make firstrun`.

## Additional configuration

The `.env` file includes a number of variables that are unset by default.

If you want emails to be sent, you'll need to set the `MAILGUN_DOMAIN`, `MAILGUN_KEY` and `MAILGUN_FROM` variables.
You will also want to set the `ADMIN_EMAIL` variable to some mailbox that you monitor.

To deploy on any host which is not localhost, you'll need to change the `HOST_BACKEND`, `HOST_FRONTEND` and `HOST_PUBLIC` variables.
These are important to make sure links work, but also to handle CORS in the browser.

## Tests

### System tests/integration tests that requires a running installation

Systests are written in python and the sources for the systests are in the api/src/systest directory (because it shares a lot of code with the api unittests). There are
tests using the api as well as selenium tests. Those tests are also run in Github actions.

You can run the tests in test containers using a one off db with:

```bash
make test
```

To run a single test, you can pass options to pytest using the `PYTEST_ADDOPTS` environment variable, for example:

```bash
PYTEST_ADDOPTS='-k "test_empty_cart_fails_purchase"' make test
```

Other test options that pytest supports can be passed using the same variable.

Or you can run against your local running environment with:

```bash
make dev-test
```

And you can also run single tests against your local running environment using you favorite test
runner (like pytest).

### Python unittests

The api directory also contains unittests that can be run standalone, they will also run when running `make test`.

### Javascript unit tests

Javascript unit tests are run when the images is build but they can also be run against the source directly
by `make test-admin-js` or `npm --prefix admin run test`.

### If everything goes wrong

If you for some reason want to remove the existing database and start from scratch you can run the command

```
make clean-nuke
```

> [!WARNING]
> This will completely wipe out all your makeradmin data!

After this you can run `make firstrun` again to set things up again.

## Development with Stripe

Create your own stripe account and add your keys to the `.env` file to allow purchases to work.

### "Paying" with fake Stripe key

You will not be able to go to the checkout unless you have a Stripe key in the .env-file. If this is set up, you can use [Stripe's fake cards](https://stripe.com/docs/testing#cards) for completing the purchase.

### Stripe - Makeradmin connection

Makeradmin is used as the truth, and Stripe is automatically synced with the makeradmin products.

### Stripe subscription support

To handle subscriptions properly, the server needs to listen to stripe webhooks and configure subscription products (see next session).
You can do this by installing the Stripe CLI and forward events using

```bash
stripe listen --forward-to http://localhost:8010/webshop/stripe_callback
```

After the forwarding has started, you'll need to copy the signing secret it gives you, and put it in your own `.env` file in the key `STRIPE_SIGNING_SECRET`.

Note: When running tests, this is not necessary, as it will poll the stripe server automatically.

## Bookkeeping and accounting

For accounting Makeradmin supports exporting the transaction history as sie files.

The transaction history is compared with Stripe to make sure it matches and there are no extra transactions in Makeradmin or Stripe.

Debit bookings adjust the product price with the transaction fee. However, each transaction usually contain multiple products. Thus, the transaction fee neds to be distributed over the products if the debit accounts or cost centers for the product are different. This adjustment involves distributing the transaction fee among the products in proportion to their total price within the transaction, which takes into consideration the quantity of products purchased. Any rounding errors are corrected by adjusting them to the nearest, higher or lower, amount. Any left over cent is added or removed on the most expensive price to make sure the total sum is correct.
