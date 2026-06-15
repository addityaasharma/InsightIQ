# 📊 InsightIQ — AI-Powered Business Data Analysis Platform

An intelligent data analysis platform that allows businesses to upload CSV/Excel files, automatically generate visual insights, and interact with their data through a conversational AI assistant powered by Hugging Face — built with Flask, PostgreSQL, and a full ML/AI stack.

---

## 🚀 Tech Stack

### Backend & API
| Technology | Purpose |
|---|---|
| Flask | Python web framework |
| Flask-RESTful | REST API structure |
| Flask-SocketIO | Real-time updates |
| Flask-JWT-Extended | Authentication |
| Flask-Limiter | Rate limiting |
| Flask-Mail | Email notifications |
| Gunicorn + Eventlet/Gevent | Production server |

### Database & Storage
| Technology | Purpose |
|---|---|
| PostgreSQL | Primary database |
| SQLAlchemy + Flask-Migrate | ORM & migrations |
| Cloudinary | File & chart storage |
| Redis | Celery task queue & caching |
| Supabase | Additional storage (optional) |

### AI / ML Stack
| Technology | Purpose |
|---|---|
| Hugging Face Hub | Conversational AI / NLP |
| scikit-learn | ML models, clustering, regression |
| TensorFlow | Deep learning predictions |
| NumPy | Numerical computation |
| Pandas | Data manipulation & analysis |
| SciPy | Statistical analysis |
| Matplotlib | Chart generation |
| Plotly | Interactive visualizations |
| openpyxl | Excel file parsing |

### Background Jobs
| Technology | Purpose |
|---|---|
| Celery | Async task processing |
| Redis | Message broker |
| APScheduler | Scheduled report generation |

### PDF & Reports
| Technology | Purpose |
|---|---|
| ReportLab | PDF report generation |
| Matplotlib / Plotly | Chart exports |

---

## 📁 Project Structure

```
insightiq-backend/
│
├── controllers/               # Business logic per feature
│   ├── auth_controller.py
│   ├── upload_controller.py
│   ├── analysis_controller.py
│   ├── ai_controller.py
│   ├── report_controller.py
│   └── dashboard_controller.py
│
├── migrations/                # Alembic DB migrations
│
├── static/
│   └── uploads/
│       ├── csv_files/         # Uploaded CSV/Excel files
│       ├── charts/            # Generated chart images
│       └── reports/           # Generated PDF reports
│
├── .env                       # Environment variables
├── config.py                  # App configuration
├── models.py                  # SQLAlchemy models
├── middleware.py              # JWT auth middleware
├── server.py                  # Flask app entry point
├── socket_instance.py         # Flask-SocketIO instance
├── leaves.py                  # (if HR module integrated)
├── masteradmin.py             # Master admin routes
├── superadmin_routes.py       # Super admin routes
├── user_route.py              # User routes
├── otp_utils.py               # OTP generation & verification
└── requirements.txt
```

---

## 🗃️ Database Schema

```
User
  └── Organisation
        ├── UploadedFile (CSV/Excel)
        │     ├── ColumnMetadata      ← detected columns, types
        │     ├── AnalysisResult      ← generated insights
        │     │     ├── Chart         ← chart image URLs (Cloudinary)
        │     │     └── Insight       ← text insight entries
        │     └── AIChatSession
        │           └── AIChatMessage ← Q&A history with AI
        │
        ├── Report                    ← generated PDF reports
        ├── Notification
        └── ScheduledReport           ← APScheduler jobs
```

---

## ⚙️ Environment Setup

### `.env`
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/insightiq_db

# JWT
SECRET_KEY=your_jwt_secret_key
JWT_EXPIRY_DAYS=7

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Hugging Face
HUGGINGFACE_API_TOKEN=hf_your_token_here
HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# App
FLASK_ENV=development
FLASK_DEBUG=1

# Razorpay (billing/subscription)
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Supabase (optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

---

## 🛠️ Installation & Running

```bash
# 1. Clone the repository
git clone <repo-url>
cd insightiq-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 5. Start Redis (required for Celery)
redis-server

# 6. Initialize database
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# 7. Start Celery worker (separate terminal)
celery -A server.celery worker --loglevel=info

# 8. Start Celery beat scheduler (separate terminal)
celery -A server.celery beat --loglevel=info

# 9. Run the Flask server
python server.py
```

---

## 📡 API Overview

### 🔐 Authentication — `/auth`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user/organisation |
| POST | `/auth/login` | Login |
| POST | `/auth/send-otp` | Send OTP to email |
| POST | `/auth/verify-otp` | Verify OTP |
| POST | `/auth/reset-password` | Reset password |
| POST | `/auth/logout` | Logout |
| GET | `/auth/profile` | Get own profile |
| PUT | `/auth/profile` | Update profile |

---

### 📂 File Upload — `/upload`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload/csv` | Upload CSV file |
| POST | `/upload/excel` | Upload Excel (.xlsx) file |
| GET | `/upload/files` | List all uploaded files |
| GET | `/upload/file/:id` | File detail + column metadata |
| DELETE | `/upload/file/:id` | Delete file |
| GET | `/upload/file/:id/preview` | Preview first 50 rows |
| GET | `/upload/file/:id/columns` | Get column names & data types |

**Supported formats:** `.csv`, `.xlsx`, `.xls`

---

### 🔍 Analysis — `/analysis`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/analysis/run/:file_id` | Run full analysis on a file |
| GET | `/analysis/:file_id` | Get analysis results |
| GET | `/analysis/:file_id/summary` | Statistical summary |
| GET | `/analysis/:file_id/charts` | All generated charts |
| GET | `/analysis/:file_id/insights` | Text insights |
| GET | `/analysis/:file_id/correlations` | Correlation matrix |
| GET | `/analysis/:file_id/trends` | Trend detection |
| GET | `/analysis/:file_id/anomalies` | Anomaly detection |
| GET | `/analysis/:file_id/forecast` | Future value predictions |
| GET | `/analysis/:file_id/clusters` | Customer/data clustering |

---

### 🤖 AI Chat — `/ai`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/ai/chat/:file_id` | Ask AI about your data |
| GET | `/ai/chat/:file_id/history` | Get chat history |
| DELETE | `/ai/chat/:file_id/history` | Clear chat history |
| POST | `/ai/summarize/:file_id` | AI text summary of data |
| POST | `/ai/recommend/:file_id` | AI business recommendations |

**Example queries:**
```
"What is the total revenue for Q3?"
"Which product has the highest return rate?"
"Show me the top 5 customers by sales"
"What are the main trends in this data?"
"Give me 3 business recommendations based on this data"
```

---

### 📊 Dashboard — `/dashboard`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/dashboard/overview` | KPI cards & summary |
| GET | `/dashboard/recent` | Recent uploads & analyses |
| GET | `/dashboard/charts` | Saved charts |
| GET | `/dashboard/activity` | User activity log |

---

### 📄 Reports — `/report`
| Method | Endpoint | Description |
|---|---|---|
| POST | `/report/generate/:file_id` | Generate PDF report |
| GET | `/report/list` | All generated reports |
| GET | `/report/:id` | Download PDF report |
| DELETE | `/report/:id` | Delete report |
| POST | `/report/schedule` | Schedule auto report |
| GET | `/report/scheduled` | List scheduled reports |
| DELETE | `/report/schedule/:id` | Cancel scheduled report |

---

### 🔔 Notifications — `/notifications`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications` | All notifications |
| PUT | `/notifications/:id/read` | Mark as read |
| PUT | `/notifications/read-all` | Mark all as read |
| DELETE | `/notifications/:id` | Delete notification |

---

### 👑 Admin — `/admin`
| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/dashboard` | Platform-wide stats |
| GET | `/admin/users` | All users |
| PUT | `/admin/user/:id` | Update user |
| DELETE | `/admin/user/:id` | Delete user |
| GET | `/admin/usage` | API & storage usage |
| GET | `/admin/subscriptions` | Billing & plans |

---

## 🧠 AI & ML Pipeline

### 1. File Upload & Parsing
```
CSV/Excel uploaded
  → Pandas reads file
  → Auto-detect column types (numeric, categorical, datetime, text)
  → Store column metadata in DB
  → Preview first 50 rows cached
```

### 2. Automatic Analysis (Celery async task)
```
Analysis triggered
  → Statistical summary (mean, median, std, min, max, quartiles)
  → Missing value detection & report
  → Correlation matrix (NumPy/Pandas)
  → Trend analysis (SciPy regression)
  → Anomaly detection (scikit-learn IsolationForest)
  → Customer segmentation (scikit-learn KMeans clustering)
  → Time-series forecasting (TensorFlow / scikit-learn)
  → Chart generation (Matplotlib + Plotly)
  → Upload charts to Cloudinary
  → Save insights to DB
  → Notify user via SocketIO
```

### 3. Chart Types Generated
| Chart | When Generated |
|---|---|
| Bar Chart | Categorical comparisons |
| Line Chart | Time-series / trends |
| Scatter Plot | Correlation between columns |
| Pie / Donut | Distribution / proportions |
| Heatmap | Correlation matrix |
| Histogram | Numeric distribution |
| Box Plot | Outlier detection |
| Cluster Plot | Segmentation results |
| Forecast Chart | Future predictions |

### 4. AI Chat (Hugging Face)
```
User asks question
  → Context built from:
      - Column names & types
      - Statistical summary
      - Top 100 rows as sample
      - Previous conversation history
  → Sent to Hugging Face model (Mistral / Llama / etc.)
  → Response returned to user
  → Stored in chat history
```

---

## 📄 PDF Report Contents

Auto-generated PDF report includes:
- Company logo & report title
- Data source info (filename, rows, columns)
- Executive summary (AI-generated)
- Key metrics & KPIs
- All generated charts (embedded)
- Statistical summary table
- Top insights (bullet points)
- Anomalies detected
- Business recommendations (AI-generated)
- Footer with generation timestamp

---

## ⏰ Scheduled Reports (APScheduler)

Users can schedule automatic report generation:

```python
# Options
frequency = ["daily", "weekly", "monthly"]
delivery  = ["email", "download", "both"]
```

Reports are generated by **Celery Beat** and emailed via **Flask-Mail** as PDF attachments.

---

## 💳 Subscription & Billing (Razorpay)

| Plan | File Uploads | AI Queries | Storage |
|---|---|---|---|
| Free | 5/month | 20/month | 100 MB |
| Pro | 50/month | 500/month | 5 GB |
| Business | Unlimited | Unlimited | 50 GB |

Payments processed via **Razorpay** integration.

---

## 🚦 Rate Limiting

```python
default_limits = ["500 per day", "100 per hour"]

# AI endpoints (heavier — limited separately)
limiter.limit("50 per day;10 per hour")  # AI chat
limiter.limit("20 per day;5 per hour")   # Report generation
```

---

## 🚀 Deployment

### Production with Gunicorn
```bash
# Install production deps
pip install gunicorn eventlet

# Run with Gunicorn + Eventlet (for SocketIO support)
gunicorn --worker-class eventlet -w 1 \
  --bind 0.0.0.0:5000 \
  --timeout 300 \
  server:app
```

> ⚠️ Use `--timeout 300` since ML analysis jobs can take longer than default 30s.

### With Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Increase timeout for ML processing
    proxy_read_timeout 300;
    proxy_connect_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        client_max_body_size 50M;  # allow large file uploads
    }
}
```

### Celery in Production
```bash
# Worker
celery -A server.celery worker --loglevel=info --concurrency=4

# Scheduler
celery -A server.celery beat --loglevel=info
```

---

## 🔒 Security

- JWT tokens with 7-day expiry
- OTP-based email verification & password reset
- Role-based access (Admin / User)
- File type validation on upload (only CSV/Excel allowed)
- File size limits enforced
- Rate limiting on all endpoints (stricter on AI/ML routes)
- Cloudinary signed URLs for secure file access
- All credentials in `.env` (never committed)

---

## 📊 Key Dependencies Summary

```txt
# Web Framework
Flask==3.1.2
Flask-RESTful==0.3.10
Flask-JWT-Extended==4.7.1
Flask-SocketIO==5.6.0
Flask-Limiter==4.1.1
Flask-Mail==0.10.0

# Database
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.1.0
psycopg2-binary==2.9.11
alembic==1.18.1

# ML / AI
numpy==2.4.3
pandas==3.0.1
scikit-learn==1.8.0
scipy==1.17.1
matplotlib==3.10.8
plotly==6.6.0
huggingface_hub==1.7.1

# Background Jobs
celery==5.6.2
redis==7.1.1
APScheduler==3.11.1

# File & Storage
cloudinary==1.44.1
openpyxl==3.1.5
reportlab==4.4.5
Pillow==12.1.0

# Production
gunicorn==25.0.3
eventlet==0.40.4

# Payments
razorpay==2.0.0
```

---

## 📄 License

This project is proprietary software developed by **Aditya Sharma**
All rights reserved © 2025 Aditya Sharma.

---

*Built with ❤️ in Bhilai, Chhattisgarh*
