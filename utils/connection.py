from dotenv import load_dotenv
import os

load_dotenv()

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
class Development(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DEV_DATABASE_URI", "postgresql://neondb_owner:npg_6BprSGbmg5vI@ep-polished-feather-ak8lzp44-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")