import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_cors import CORS
from utils.config import db, migrate, limiter
from utils.connection import Development
from utils.celery.celery_app import init_celery
from routes.route import user

load_dotenv()

app = Flask(__name__)
app.config.from_object(Development)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

db.init_app(app)
migrate.init_app(app, db)
limiter.init_app(app)
init_celery(app)
# ✅ Fix in app.py
CORS(app,
    supports_credentials=True,
    resources={r"/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://your-production-frontend.com",  # add your deployed URL
        ]
    }}
)

app.register_blueprint(user)
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
