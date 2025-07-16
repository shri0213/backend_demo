
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

# ✅ Load environment variables
load_dotenv()

# ✅ Get full PostgreSQL URL directly
DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
