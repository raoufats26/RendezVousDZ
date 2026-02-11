from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO, emit, join_room, leave_room

from routes.auth import auth_bp
from routes.booking import booking_bp

app = Flask(__name__)
app.secret_key = "dqsjhlfqksÃ¹*&Ã©&Ã©'_&Ã "

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

app.register_blueprint(auth_bp)
app.register_blueprint(booking_bp)

# ========================================
# SOCKETIO EVENT HANDLERS
# ========================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected')

@socketio.on('join')
def handle_join(data):
    """Handle client joining a business-specific room"""
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
    """Handle 404 errors with a friendly message"""
    return render_template("public_booking.html", 
                         error="Page not found", 
                         business=None), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors gracefully"""
    return render_template("public_booking.html", 
                         error="An error occurred. Please try again later.", 
                         business=None), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all handler for unexpected errors"""
    # Log the error for debugging (in production, use proper logging)
    print(f"Unexpected error: {str(e)}")
    
    return render_template("public_booking.html", 
                         error="An unexpected error occurred. Please try again.", 
                         business=None), 500

if __name__ == "__main__":
    # Use socketio.run() instead of app.run()
    socketio.run(app, debug=True)
