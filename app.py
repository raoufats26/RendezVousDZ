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
    app.run(debug=True)
