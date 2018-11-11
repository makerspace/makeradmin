from flask import Flask

import frontend
import member
from service import format_datetime

app = Flask(__name__, static_url_path="/static")
app.jinja_env.filters['format_datetime'] = format_datetime
app.register_blueprint(frontend.instance.blueprint)
app.register_blueprint(member.instance.blueprint)


@app.route("/")
def root():
    return "This is the root!"


@app.context_processor
def static():
    return dict(STATIC="/static")
