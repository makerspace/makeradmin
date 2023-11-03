[![Build and run tests for makeradmin](https://github.com/makerspace/makeradmin/actions/workflows/makeradmin.yml/badge.svg)](https://github.com/makerspace/makeradmin/actions/workflows/makeradmin.yml)
# Makeradmin

## Install 

### Docker
```bash
sudo apt-get install docker.io docker-compose-plugin
sudo adduser your_username docker
```
You need to sign out and sign back in again for changes to take effect. 

### Python
Python 3.10.

The install process will install additional pip packages.
Activate a venv / virtualenv before install if you want python environment isolation.

### npm
```bash
sudo apt-get install npm
```

## Initialize everything
```bash
make firstrun
```

This will build docker images and configure the database. This may take quite some time.
It will also generate a `.env` file with new random keys and passwords that the system will use.

You will be prompted for if you want to create a new admin user, it is recommended to do this here.

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
* [the makeradmin web site](http://localhost:8009)
* [the web shop](http://localhost:8011/shop)

### Logging in
Go to [the member page](http://localhost:8011/member) and fill in the email address corresponding to the user created previously. A link will then be printed in the terminal (where `make dev` is run) that allows you to login. E.g.

```
[...]
public_1            | 10.0.2.2 - - [18/Dec/2018:20:50:23 +0000] "GET / HTTP/1.1" 302 223 "http://localhost:8011/member/login/XHCgGQZGrjuG6bO7TVPkikTfQVRo6Eqn?redirect=%2Fmember" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"
[...]
```

## Additional configuration

The `.env` file includes a number of variables that are unset by default.

If you want emails to be sent, you'll need to set the `MAILGUN_DOMAIN`, `MAILGUN_KEY` and `MAILGUN_FROM` variables.
You will also want to set the `ADMIN_EMAIL` variable to some mailbox that you monitor.

To deploy on any host which is not localhost, you'll need to change the `HOST_BACKEND`, `HOST_FRONTEND` and `HOST_PUBLIC` variables.
These are important to make sure links work, but also to handle CORS in the browser.

## Tests

### System tests/integration tests that requires a running installation

Systests are written in python and the sources for the systests are in the api/src/systest directory (because it shares a lot of code with the api unittests). There are 
tests using the api as well as selenium tests. Those tests are also run in travis.

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

### Python unittests

The api directory also contains unittests that can be run standalone, they will also run when running ```make test```.

### Javascript unit tests

Javascript unit tests are run when the images is build but they can also be run against the source directly
by ```make test-admin-js``` or ```npm --prefix admin run test```.


### If everything goes wrong

If you for some reason want to remove the existing database and start from scratch you can run the command
```
make clean-nuke
```

*Warning: this will completely wipe out all your makeradmin data!*

After this you can run `make firstrun` again to set things up again.

## Development with Stripe

Create your own stripe account and add your keys to the `.env` file to allow purchases to work.

### "Paying" with fake Stripe key

You will not be able to go to the checkout unless you have a Stripe key in the .env-file. If this is set up, you can use [Stripe's fake cards](https://stripe.com/docs/testing#cards) for completing the purchase.

### Stripe subscription support

To handle subscriptions properly, the server needs to listen to stripe webhooks and configure subscription products (see next session).
You can do this by installing the Stripe CLI and forward events using

```bash
stripe listen --forward-to http://localhost:8010/webshop/stripe_callback
```

After the forwarding has started, you'll need to copy the signing secret it gives you, and put it in your own `.env` file in the key `STRIPE_SIGNING_SECRET`.

### Setting up Stripe subscription products

When using stripe, subscriptions need to be configured via the stripe website.
These subscriptions will automatically be turned into makeradmin products so that members can purchase them.

Note: You should *not* modify these products in makeradmin. They will be reset whenever the docker container restarts anyway (when the registration page is visited).

The configuration needed on stripe is:

* Create a **product** for base membership. Add the metadata "subscription_type"="membership" to the **product** item
  * Add a yearly **price**, and add the metadata "price_type"="recurring" to the **price** item
* Create a **product** for makerspace access. Add the metadata "subscription_type"="labaccess" to the **product** item
  * Add a monthly price, and add the metadata "price_type"="recurring" to the **price** item
  * Add a **price** for N months, where N is the binding period as specified in `stripe_subscriptions.py->BINDING_PERIOD`. The price should be N times the recurring price. Add the metadata "price_type"="binding_period"
* Create a **coupon** for low income discount. It should be with percentage discount. Add the metadata "makerspace_price_level" = "low_income_discount"

If you try to access any page which needs these products (e.g. the registration page, or the member page), makeradmin will fetch them from stripe and do a bunch of validation checks.

### Setting up required products in makeradmin

For the member view page and regristration page to work there are also a few products needed in makeradmin in the category Medlemskap.

* Base membership
  * Metadata: {"allowed_price_levels":["low_income_discount"],"special_product_id":"single_membership_year"}
  * Action: add membership days
* Makerspace access
  * Metadata: {"allowed_price_levels":["low_income_discount"],"special_product_id":"single_labaccess_month"}
  * Action: add membership days, add labaccess days
* Makerspace access starter pack
  * Metadata:{"allowed_price_levels":["low_income_discount"],"special_product_id":"access_starter_pack"}
  * Action: add labaccess days
