import secrets

config = {
    "MYSQL_DB": "makerdata",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "testuser",
    "MYSQL_PASS": secrets.token_hex(16),
    "MYSQL_ROOT_PASSWORD": secrets.token_hex(16),
    # Note: This must fit into the access_tokens table in the database
    "API_BEARER": secrets.token_hex(16),
    "TICTAIL_USER": "",
    "TICTAIL_PASS": "",
    "TICTAIL_STORE": "",
    "MAILGUN_DOMAIN": "",
    "MAILGUN_KEY": "",
    "MAILGUN_FROM": "Excited User <excited@samples.mailgun.org>",
    "MAILGUN_TO_OVERRIDE": "",
    "HOST_BACKEND": "localhost:8010",
    "HOST_FRONTEND": "localhost:8009",
}

with open(".env", "w") as f:
    f.write("\n".join(key + "=" + value for (key, value) in config.items()))
