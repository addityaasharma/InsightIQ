from utils.config import db
from sqlalchemy import Enum as SQLEnum
from enum import Enum


class UserRole(Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    WORKING_PROFESSIONAL = "working_professional"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(
        SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
        default=UserRole.STUDENT,
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    datasets = db.relationship(
        "Dataset", back_populates="user", cascade="all, delete-orphan", lazy=True
    )


class Dataset(db.Model):
    __tablename__ = "dataset"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_rows = db.Column(db.Integer)
    file_columns = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user = db.relationship("User", back_populates="datasets")
    columns = db.relationship(
        "DatasetColumn", back_populates="dataset", cascade="all, delete-orphan"
    )
    charts = db.relationship(
        "Chart", back_populates="dataset", cascade="all, delete-orphan"
    )
    predictions = db.relationship(
        "Prediction", back_populates="dataset", cascade="all, delete-orphan"
    )
    insights = db.relationship(
        "Insight", back_populates="dataset", cascade="all, delete-orphan"
    )
    business_scores = db.relationship(
        "BusinessScore", back_populates="dataset", cascade="all, delete-orphan"
    )
    data_questions = db.relationship(
        "DataQuestion", back_populates="dataset", cascade="all, delete-orphan", uselist=True
    )


class DatasetColumn(db.Model):
    __tablename__ = "dataset_columns"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    column_name = db.Column(db.String(100))
    data_type = db.Column(db.String(50))
    is_numeric = db.Column(db.Boolean)
    is_date = db.Column(db.Boolean)
    dataset = db.relationship("Dataset", back_populates="columns")


class Chart(db.Model):
    __tablename__ = "charts"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    chart_type = db.Column(db.String(50))
    chart_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    dataset = db.relationship("Dataset", back_populates="charts")


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    model_used = db.Column(db.String(50))
    prediction_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    dataset = db.relationship("Dataset", back_populates="predictions")


class Insight(db.Model):
    __tablename__ = "insights"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    insight_type = db.Column(db.String(50))
    insight_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    dataset = db.relationship("Dataset", back_populates="insights")


class BusinessScore(db.Model):
    __tablename__ = "business_scores"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    profitability_score = db.Column(db.Float)
    growth_score = db.Column(db.Float)
    risk_score = db.Column(db.Float)
    recommendation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    dataset = db.relationship("Dataset", back_populates="business_scores")


class DataQuestion(db.Model):
    __tablename__ = "data_questions"
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False
    )
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    context_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    dataset = db.relationship("Dataset", back_populates="data_questions")
