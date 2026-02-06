from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from routes.auth import auth_bp
from routes.booking import booking_bp

app = Flask(__name__)
app.secret_key = "dqsjhlfqksù*&é&é'_&à"

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)
