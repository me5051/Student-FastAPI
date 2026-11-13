import os

from dotenv import load_dotenv
from pwdlib import PasswordHash

from pydantic import BaseModel, EmailStr, Field
from pathlib import Path
from datetime import datetime, timezone, timedelta

import jwt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    Session,
    sessionmaker,
)

app = FastAPI(title="Student Management API")

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

BASE_DIR = Path(__file__).resolve().parents[1]

DB_PATH = BASE_DIR / "students.db"
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ADMIN_CODE = os.getenv("ADMIN_REGISTRATION_CODE", "classroom-admin-code")
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

class Base(DeclarativeBase):
    pass

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    course: Mapped[str] = mapped_column(String(100))

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), default="student")
    
from sqlalchemy.orm import Session, sessionmaker
engine = create_engine(f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False})

class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    admin_code: str | None = None
    
class StudentInput(BaseModel):
    name: str
    email: EmailStr
    course: str
    
class StudentOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    course: str

    class Config:
        from_attributes = True
    
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

# @app.get("/students")
# def list_students(db: Session = Depends(get_db)):
#  statement = select(Student).order_by(Student.name)
#  rows = db.scalars(statement).all()
#  return rows

# student = Student(name="Ada Okafor",
#         email="ada@example.test",
#         course="Year 2"
# )

# db.add(student) # stage this new row in the session
# db.commit() # save the change in the database
# db.refresh(student) # read generated values such as id

# student = db.get(Student, student_id)
# if student is None:
#     raise HTTPException(status_code=404, detail="Student not found")
# student.course = "Year 3"
# db.commit()

# student = db.get(Student, student_id)
# if student is None:
#     raise HTTPException(status_code=404, detail="Student not found")
# db.delete(student)
# db.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
def make_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
 
def current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(data["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired login")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Account not found")
    return user

def admin_only(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user

@app.post("/auth/register", status_code=201)
def register(data: RegisterInput, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    role = "student"
    if data.admin_code:
        if data.admin_code != ADMIN_CODE:
            raise HTTPException(status_code=403, detail="Incorrect admin registration code")
        role = "admin"
    user = User(email=email, password_hash=password_hash.hash(data.password), role=role)
    db.add(user)
    db.commit()
    return {"message": "Account created", "role": role}

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form.username.strip().lower() # OAuth form calls this field username
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not password_hash.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": make_token(user), "token_type": "bearer", "role": user.role}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
def make_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
 
def current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(data["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired login")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Account not found")
    return user

def admin_only(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user

@app.post("/auth/register", status_code=201)
def register(data: RegisterInput, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    role = "student"
    if data.admin_code:
        if data.admin_code != ADMIN_CODE:
            raise HTTPException(status_code=403, detail="Incorrect admin registration code")
        role = "admin"
    user = User(email=email, password_hash=password_hash.hash(data.password), role=role)
    db.add(user)
    db.commit()
    return {"message": "Account created", "role": role}

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form.username.strip().lower() # OAuth form calls this field username
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not password_hash.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": make_token(user), "token_type": "bearer", "role": user.role}

@app.get("/students", response_model=list[StudentOut])
def list_students(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    return db.scalars(
        select(Student).order_by(Student.name)
    ).all()
    
@app.post("/students", response_model=StudentOut, status_code=201)
def add_student(
    data: StudentInput,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    email = data.email.strip().lower()
    if db.scalar(select(Student).where(Student.email == email)):
        raise HTTPException(status_code=409, detail="Student email already exists")
    student = Student(name=data.name.strip(), email=email, course=data.course.strip())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    data: StudentInput,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only)
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    email = data.email.strip().lower()

    existing = db.scalar(
        select(Student).where(
            Student.email == email,
            Student.id != student_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Student email already exists"
        )

    student.name = data.name.strip()
    student.email = email
    student.course = data.course.strip()

    db.commit()
    db.refresh(student)

    return student

@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only)
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}

