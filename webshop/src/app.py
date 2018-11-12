import os

from flask import Flask, redirect, url_for

import frontend
import member
from service import format_datetime

app = Flask(__name__, static_url_path="/static")
app.jinja_env.filters['format_datetime'] = format_datetime
app.register_blueprint(frontend.instance.blueprint)
app.register_blueprint(member.instance.blueprint)


@app.route("/")
def root():
    return redirect(url_for("member.member"))


host_backend = os.environ["HOST_BACKEND"]
if not host_backend.startswith("http"):
    host_backend = "https://" + host_backend


@app.context_processor
def context():
    return dict(
        STATIC="/static",
        meta=dict(
            apiBasePath=host_backend,
            stripePublicKey=os.environ["STRIPE_PUBLIC_KEY"],
        )
    )


