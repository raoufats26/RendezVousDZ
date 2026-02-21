import os
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room

from routes.auth import auth_bp
from routes.booking import booking_bp
from routes.analytics import analytics_bp          # PHASE 16
from routes.display import display_bp              # PHASE 16 digital display

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dqsjhlfqksmù*&é&é'_& ")

# ---------------------------
# FLASK-MAIL CONFIGURATION
# ---------------------------
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER',         'smtp.gmail.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT',       587))
app.config['MAIL_USE_TLS']        = os.environ.get('MAIL_USE_TLS',        'true').lower() == 'true'
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME',       '')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD',       '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@rendezvousdz.com')

try:
    from flask_mail import Mail
    mail = Mail(app)
except ImportError:
    pass  # flask-mail optional until configured

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(analytics_bp)              # PHASE 16
app.register_blueprint(display_bp)                # PHASE 16 digital display

# Simple i18n shim — templates can use _('text'), returns text as-is
def _(s): return s
app.jinja_env.globals['_'] = _

# ========================================
# SOCKETIO EVENT HANDLERS
# ========================================

@socketio.on('connect')
def handle_connect():
    print(f'Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected')

@socketio.on('join')
def handle_join(data):
    business_id = data.get('business_id')
    if business_id:
        room = f'business_{business_id}'
        join_room(room)
        print(f'Client joined room: {room}')
        emit('joined', {'room': room})

@app.route("/")
def home():
    return render_template("home.html")

# ========================================
# GLOBAL ERROR HANDLERS
# ========================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("public_booking.html",
                           error="Page not found", business=None), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("public_booking.html",
                           error="An error occurred. Please try again later.", business=None), 500

@app.errorhandler(Exception)
def handle_exception(e):
    print(f"Unexpected error: {str(e)}")
    return render_template("public_booking.html",
                           error="An unexpected error occurred. Please try again.", business=None), 500

if __name__ == "__main__":
    socketio.run(app, debug=True)
