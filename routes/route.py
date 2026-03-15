import os, io
import requests
from model import *
import pandas as pd, jwt, datetime
from utils.config import db
from utils.config import UPLOAD_FOLDER, limiter
from flask import Blueprint, request, jsonify, g, make_response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from services.middleware import middleware
from services.analysis_service import analyze_dataset
from services.huggingface_service import generate_text
from services.supabase_service import upload_csv_to_supabase


user = Blueprint("analytics", __name__, url_prefix="/user")


@user.route("/signup", methods=["POST"])
@limiter.limit("5 per minute")
def signup():
    try:
        data = request.get_json()

        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if not data.get(field):
                return (
                    jsonify({"status": "error", "message": f"{field} is required"}),
                    400,
                )

        check_user = User.query.filter_by(username=data["username"]).first()
        if check_user:
            return (
                jsonify({"status": "error", "message": "Username already exists"}),
                400,
            )

        if data["role"] not in UserRole._value2member_map_:
            return jsonify({"status": "error", "message": "Invalid role"}), 400

        hash_password = generate_password_hash(data["password"], method="pbkdf2:sha256")

        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hash_password,
            role=UserRole(data["role"]),
        )
        db.session.add(new_user)
        db.session.commit()

        payload = {
            "customer_id": new_user.id,
            "customer_email": new_user.email,
            "customer_role": new_user.role.value,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        }

        token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
        response = make_response(
            jsonify(
                {
                    "status": "success",
                    "message": "User created successfully",
                }
            ),
            201,
        )

        response.set_cookie(
            "token",
            token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=24 * 60 * 60,
        )
        return response
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {"status": "error", "message": "Failed to signup", "error": str(e)}
            ),
            500,
        )


@user.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    try:
        data = request.get_json()

        required_fields = ["email", "password"]
        for field in required_fields:
            if not data.get(field):
                return (
                    jsonify({"status": "error", "message": f"{field} is required"}),
                    400,
                )

        check_user = User.query.filter_by(email=data["email"]).first()
        if not check_user or not check_password_hash(
            check_user.password, data["password"]
        ):
            return (
                jsonify({"status": "error", "message": "Invalid email or password"}),
                401,
            )

        payload = {
            "customer_id": check_user.id,
            "customer_email": check_user.email,
            "customer_role": check_user.role.value,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        }

        token = jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
        response = make_response(
            jsonify(
                {
                    "status": "success",
                    "message": "Login successful",
                    "id": check_user.id,
                }
            ),
            200,
        )

        response.set_cookie(
            "token",
            token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=24 * 60 * 60,
        )

        return response
    except Exception as e:
        db.session.rollback()
        return (
            jsonify({"status": "error", "message": "Failed to login", "error": str(e)}),
            500,
        )


@user.route("/", methods=["POST"])
@middleware
def upload_csv():
    userID = g.user_id
    if not userID:
        return jsonify({"status": "error", "message": "Unauthorized"}), 400

    try:
        file = request.files.get("file")
        if not file or not file.filename.endswith(".csv"):
            return jsonify({"status": "error", "message": "Invalid file format"}), 400

        filename = secure_filename(file.filename)
        file_path = upload_csv_to_supabase(file)
        file.seek(0)

        df = pd.read_csv(file_path)

        dataset = Dataset(
            user_id=userID,
            file_name=filename,
            file_path=file_path,
            file_rows=df.shape[0],
            file_columns=df.shape[1],
        )

        db.session.add(dataset)
        db.session.commit()

        try:
            analysis = analyze_dataset(dataset, file_path)
        except Exception as e:
            return (
                jsonify(
                    {"status": "error", "message": "Analysis failed", "error": str(e)}
                ),
                500,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Dataset analyzed successfully",
                    "data": {
                        "dataset_id": dataset.id,
                        "rows": dataset.file_rows,
                        "columns": dataset.file_columns,
                        "analysis": analysis,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()

        return (
            jsonify(
                {"status": "error", "message": "Failed to upload CSV", "error": str(e)}
            ),
            500,
        )


@user.route("/question/<int:dataset_id>", methods=["POST"])
def ask_question(dataset_id):
    try:
        if not dataset_id:
            return (
                jsonify({"status": "error", "message": "Dataset ID is required"}),
                400,
            )

        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        question = data.get("question")
        if not question:
            return jsonify({"status": "error", "message": "Question is required"}), 400

        # Fetch dataset
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({"status": "error", "message": "Dataset not found"}), 404

        prediction = Prediction.query.filter_by(dataset_id=dataset_id).first()
        prediction_context = prediction.prediction_data if prediction else {}

        insights = Insight.query.filter_by(
            dataset_id=dataset_id, insight_type="ai_analysis"
        ).all()
        insights_context = [i.insight_data.get("text", "") for i in insights]

        anomalies = Insight.query.filter_by(
            dataset_id=dataset_id, insight_type="anomaly"
        ).all()
        anomalies_context = [
            {
                "column": a.insight_data.get("column"),
                "count": a.insight_data.get("count"),
            }
            for a in anomalies
        ]

        score = BusinessScore.query.filter_by(dataset_id=dataset_id).first()
        score_context = (
            {
                "profitability": score.profitability_score,
                "growth": score.growth_score,
                "risk": score.risk_score,
                "recommendation": score.recommendation,
            }
            if score
            else {}
        )

        columns = DatasetColumn.query.filter_by(dataset_id=dataset_id).all()
        columns_context = [
            {"name": c.column_name, "type": c.data_type, "is_numeric": c.is_numeric}
            for c in columns
        ]

        context_data = {
            "dataset": {
                "file_name": dataset.file_name,
                "rows": dataset.file_rows,
                "columns": dataset.file_columns,
            },
            "columns": columns_context,
            "prediction": prediction_context,
            "insights": insights_context,
            "anomalies": anomalies_context,
            "business_score": score_context,
        }

        # --- Build prompt and call AI ---
        prompt = f"""
You are a business data analyst assistant. 
A user has uploaded a dataset and you have access to its analysis results.

Dataset Info:
- File: {context_data['dataset']['file_name']}
- Rows: {context_data['dataset']['rows']}, Columns: {context_data['dataset']['columns']}

Columns: {context_data['columns']}

Prediction Data: {context_data['prediction']}

AI Insights: {chr(10).join(context_data['insights'])}

Anomalies Detected: {context_data['anomalies']}

Business Score:
- Profitability: {score_context.get('profitability')}
- Growth: {score_context.get('growth')}
- Risk: {score_context.get('risk')}
- Recommendation: {score_context.get('recommendation')}

Based on the above analysis, answer the following question clearly and concisely:
Question: {question}
"""

        answer = generate_text(prompt, max_tokens=400)

        data_question = DataQuestion(
            dataset_id=dataset_id,
            question=question,
            answer=answer,
            context_data=context_data,
        )
        db.session.add(data_question)
        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "question": question,
                        "answer": answer,
                        # "context_used": context_data,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to answer question",
                    "error": str(e),
                }
            ),
            500,
        )


@user.route("/<int:dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return jsonify({"status": "error", "message": "Dataset not found"}), 404

        columns = DatasetColumn.query.filter_by(dataset_id=dataset_id).all()
        charts = Chart.query.filter_by(dataset_id=dataset_id).all()
        prediction = Prediction.query.filter_by(dataset_id=dataset_id).first()
        all_insights = Insight.query.filter_by(dataset_id=dataset_id).all()
        business_score = BusinessScore.query.filter_by(dataset_id=dataset_id).first()
        questions = DataQuestion.query.filter_by(dataset_id=dataset_id).all()

        ai_insights = [i for i in all_insights if i.insight_type == "ai_analysis"]
        anomalies = [i for i in all_insights if i.insight_type == "anomaly"]

        univariate_anomalies = [
            a for a in anomalies if a.insight_data.get("column") != "__multivariate__"
        ]
        multivariate_anomalies = [
            a for a in anomalies if a.insight_data.get("column") == "__multivariate__"
        ]

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "dataset": {
                            "id": dataset.id,
                            "file_name": dataset.file_name,
                            "file_rows": dataset.file_rows,
                            "file_url": dataset.file_path,
                            "file_columns": dataset.file_columns,
                            "created_at": dataset.created_at,
                        },
                        "columns": [
                            {
                                "name": col.column_name,
                                "type": col.data_type,
                                "is_numeric": col.is_numeric,
                                "is_date": col.is_date,
                            }
                            for col in columns
                        ],
                        "charts": [
                            {
                                "id": chart.id,
                                "type": chart.chart_type,
                                "data": chart.chart_data,
                            }
                            for chart in charts
                        ],
                        "prediction": (
                            {
                                "id": prediction.id,
                                "model_used": prediction.model_used,
                                "target_column": prediction.prediction_data.get(
                                    "target_column"
                                ),
                                "future_predictions": prediction.prediction_data.get(
                                    "future_predictions", []
                                ),
                                "model_performance": prediction.prediction_data.get(
                                    "model_performance", {}
                                ),
                                "feature_importance": prediction.prediction_data.get(
                                    "feature_importance", {}
                                ),
                                "business_insight": prediction.prediction_data.get(
                                    "business_insight", {}
                                ),
                            }
                            if prediction
                            else None
                        ),
                        "insights": [
                            {
                                "id": i.id,
                                "text": i.insight_data.get("text", ""),
                            }
                            for i in ai_insights
                        ],
                        "anomalies": [
                            {
                                "id": a.id,
                                "column": a.insight_data.get("column"),
                                "anomaly_count": a.insight_data.get("anomaly_count"),
                                "anomaly_rate_pct": a.insight_data.get(
                                    "anomaly_rate_pct"
                                ),
                                "column_stats": a.insight_data.get("column_stats", {}),
                                "severity_summary": a.insight_data.get(
                                    "severity_summary", {}
                                ),
                                "consensus_anomalies": a.insight_data.get(
                                    "consensus_anomalies", []
                                ),
                                "detection_methods": a.insight_data.get(
                                    "detection_methods", {}
                                ),
                            }
                            for a in univariate_anomalies
                        ],
                        "multivariate_anomalies": (
                            {
                                "anomaly_count": multivariate_anomalies[
                                    0
                                ].insight_data.get("anomaly_count"),
                                "anomaly_rate_pct": multivariate_anomalies[
                                    0
                                ].insight_data.get("anomaly_rate_pct"),
                                "isolation_forest": multivariate_anomalies[
                                    0
                                ].insight_data.get("isolation_forest", {}),
                                "local_outlier_factor": multivariate_anomalies[
                                    0
                                ].insight_data.get("local_outlier_factor", {}),
                                "consensus_anomalies": multivariate_anomalies[
                                    0
                                ].insight_data.get("consensus_anomalies", []),
                            }
                            if multivariate_anomalies
                            else None
                        ),
                        "business_score": (
                            {
                                "profitability": business_score.profitability_score,
                                "growth": business_score.growth_score,
                                "risk": business_score.risk_score,
                                "recommendation": business_score.recommendation,
                            }
                            if business_score
                            else None
                        ),
                        "questions": [
                            {
                                "id": q.id,
                                "question": q.question,
                                "answer": q.answer,
                                "created_at": q.created_at,
                            }
                            for q in questions
                        ],
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to fetch dataset",
                    "error": str(e),
                }
            ),
            500,
        )


@user.route("/queries", methods=["GET"])
@middleware
def get_queries():
    try:
        userID = g.user_id
        if not userID:
            return jsonify({"status": "error", "message": "Unauthorized"}), 400

        check_user = User.query.get(userID)
        if not check_user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        # page from query params
        page = request.args.get("page", 1, type=int)
        per_page = 10

        datasets = (
            Dataset.query
            .filter_by(user_id=userID)
            .order_by(Dataset.created_at.desc())  # latest first
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        if not datasets.items:
            return jsonify({
                "status": "success",
                "message": "No datasets found",
                "datasets": []
            }), 200

        return jsonify({
            "status": "success",
            "message": "Datasets found",
            "page": page,
            "total_pages": datasets.pages,
            "total_datasets": datasets.total,
            "datasets": [
                {
                    "id": d.id,
                    "name": d.file_name,
                    "path": d.file_path,
                    "created_at": d.created_at,
                }
                for d in datasets.items
            ]
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to fetch queries",
            "error": str(e),
        }), 500


@user.route("/profile", methods=["GET"])
@middleware
def get_profile():
    try:
        userID = g.user_id
        if not userID:
            return jsonify({"status": "error", "message": "Unauthorized"}), 400
        
        check_user = User.query.get(userID)
        if not check_user:
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        return jsonify({
            "status": "success",
            "message": "User profile fetched",
            "user": {
                "id": check_user.id,
                "username": check_user.username,
                "email": check_user.email,
                "role": check_user.role.value,
                "created_at": check_user.created_at,
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Failed to fetch profile",
                    "error": str(e),
                }
            ),
            500,
        )
