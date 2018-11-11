from flask import render_template
from service import create_frontend
import os


instance = create_frontend("member", url="member", port=None)

host_backend = os.environ["HOST_BACKEND"]
if not host_backend.startswith("http"):
    host_backend = "https://" + host_backend

meta = {
    "apiBasePath": host_backend,
}


@instance.route("/")
def member():
    return render_template("member.html", meta=meta)
