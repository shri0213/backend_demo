from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, User
from pydantic import BaseModel
from typing import List

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Gmail Credentials from .env
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

print("✅ EMAIL_USER from .env:", SENDER_EMAIL)
print("✅ EMAIL_PASSWORD from .env:", SENDER_PASSWORD)



# DB setup
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Temporary OTP Storage
otp_storage = {}

# Gmail Credentials (replace with real ones)
SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Serve index.html
@app.get("/")
def serve_form():
    return FileResponse("templates/index.html")

# Submit Form and Send OTP
@app.post("/submit")
def submit_form(request: Request, name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {
        "otp": otp,
        "name": name,
        "phone": phone
    }
    send_otp_email(email, otp)
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})

@app.post("/request-otp")
def request_otp(request: Request, name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {
        "otp": otp,
        "name": name,
        "phone": phone
    }
    send_otp_email(email, otp)
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})




# Verify OTP and Save to DB
@app.post("/verify")
def verify_otp(request: Request, otp_input: str = Form(...), email: str = Form(...)):
    if email in otp_storage and otp_storage[email]["otp"] == otp_input:
        db: Session = SessionLocal()
        user = User(name=otp_storage[email]["name"], email=email)
        db.add(user)
        db.commit()
        db.close()
        del otp_storage[email]
        return templates.TemplateResponse("success.html", {"request": request})
    return templates.TemplateResponse("verify.html", {"request": request, "email": email, "error": "❌ Invalid OTP"})

# Email Function
def send_otp_email(to_email, otp):
    print("📤 Sending OTP to:", to_email)     # ✅ Ye line daalo
    print("📨 OTP is:", otp)                  # ✅ Ye bhi daalo

    subject = "OTP Verification"
    body = f"Your OTP is: {otp}"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print("✅ OTP sent to visitor.")
    except Exception as e:
        print("❌ Email failed:", e)
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")


# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        orm_mode = True

# Optional: API Routes
@app.get("/users/", response_model=List[UserRead])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
