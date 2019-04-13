from flask import Flask

import maker_statistics


app = Flask(__name__)
app.register_blueprint(maker_statistics.instance.blueprint)
