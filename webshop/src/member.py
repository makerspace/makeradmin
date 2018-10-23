from flask import render_template
from service import eprint, create_frontend
import os
from typing import List, Dict, Any, Tuple


instance = create_frontend(url="member", port=8001)

host_backend = os.environ["HOST_BACKEND"]
if not host_backend.startswith("http"):
    host_backend = "https://" + host_backend

meta = {
    "apiBasePath": host_backend,
}

@instance.route("/")
def member():
	return render_template("member.html", url=instance.full_path, meta=meta)