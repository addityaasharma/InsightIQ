from functools import wraps
from flask import request, jsonify, g
import jwt, os, time
from dotenv import load_dotenv

load_dotenv()
secret_key = os.getenv("SECRET_KEY")


def middleware(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return jsonify({"error": "Token is missing!"}), 401

        try:
            payload = jwt.decode(
                token, secret_key, algorithms=["SHA256"], options={"require": ["exp"]}
            )
            if payload["exp"] < time.time():
                return jsonify({"error": "Token has expired!"}), 401

            g.user_id = payload["user_id"]

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token!"}), 401

        return f(*args, **kwargs)

    return wrapper
